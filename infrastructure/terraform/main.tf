# Kopitar NHL Analytics Platform - Main Terraform Configuration
# Production-ready infrastructure for 40+ years NHL data analysis

terraform {
  required_version = ">= 1.5"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.20"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.10"
    }
  }
  
  backend "s3" {
    bucket         = "kopitar-terraform-state"
    key            = "production/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "kopitar-terraform-lock"
  }
}

# AWS Provider Configuration
provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "Kopitar"
      Environment = var.environment
      ManagedBy   = "Terraform"
      Owner       = "DevOps-Team"
      CostCenter  = "Analytics"
    }
  }
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

# Local values
locals {
  name            = "kopitar-${var.environment}"
  region          = var.aws_region
  cluster_version = "1.28"
  
  vpc_cidr = "10.0.0.0/16"
  azs      = slice(data.aws_availability_zones.available.names, 0, 3)
  
  tags = {
    Environment = var.environment
    Project     = "Kopitar"
  }
}

# VPC Module
module "vpc" {
  source = "./modules/vpc"
  
  name = local.name
  cidr = local.vpc_cidr
  azs  = local.azs
  
  private_subnets  = ["10.0.11.0/24", "10.0.12.0/24", "10.0.13.0/24"]
  public_subnets   = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  database_subnets = ["10.0.21.0/24", "10.0.22.0/24", "10.0.23.0/24"]
  
  enable_nat_gateway   = true
  enable_vpn_gateway   = false
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  # VPC Flow Logs
  enable_flow_log                      = true
  create_flow_log_cloudwatch_iam_role  = true
  create_flow_log_cloudwatch_log_group = true
  
  tags = local.tags
}

# EKS Cluster
module "eks" {
  source = "./modules/eks"
  
  cluster_name    = "${local.name}-cluster"
  cluster_version = local.cluster_version
  
  vpc_id                         = module.vpc.vpc_id
  subnet_ids                     = module.vpc.private_subnets
  cluster_endpoint_public_access = true
  
  # Managed Node Groups
  node_groups = {
    api_nodes = {
      name           = "api-nodes"
      instance_types = ["t3.large"]
      min_size       = 3
      max_size       = 20
      desired_size   = 6
      
      k8s_labels = {
        workload = "api"
      }
      
      taints = []
    }
    
    worker_nodes = {
      name           = "worker-nodes"
      instance_types = ["c5.2xlarge"]
      min_size       = 2
      max_size       = 10
      desired_size   = 4
      
      k8s_labels = {
        workload = "worker"
      }
      
      taints = []
    }
    
    streaming_nodes = {
      name           = "streaming-nodes"
      instance_types = ["m5.xlarge"]
      min_size       = 2
      max_size       = 8
      desired_size   = 3
      
      k8s_labels = {
        workload = "streaming"
      }
      
      taints = []
    }
  }
  
  # IRSA for AWS Load Balancer Controller
  enable_irsa = true
  
  tags = local.tags
}

# RDS PostgreSQL
module "rds" {
  source = "./modules/rds"
  
  identifier = "${local.name}-postgres"
  
  engine         = "postgres"
  engine_version = "15.4"
  instance_class = "db.r6g.2xlarge"
  
  allocated_storage     = 1000
  max_allocated_storage = 5000
  storage_type          = "gp3"
  iops                  = 12000
  
  db_name  = "kopitar"
  username = var.db_username
  password = var.db_password
  port     = 5432
  
  vpc_security_group_ids = [module.security_groups.database_sg_id]
  db_subnet_group_name   = module.vpc.database_subnet_group
  
  # Multi-AZ and backups
  multi_az               = true
  backup_retention_period = 30
  backup_window          = "03:00-04:00"
  maintenance_window     = "Sun:04:00-Sun:05:00"
  
  # Read replicas
  create_read_replica = true
  read_replica_config = {
    identifier         = "${local.name}-postgres-replica"
    instance_class     = "db.r6g.xlarge"
    availability_zone  = local.azs[1]
  }
  
  # Monitoring
  monitoring_interval = 60
  monitoring_role_arn = module.iam.rds_monitoring_role_arn
  
  # Encryption
  storage_encrypted   = true
  kms_key_id         = module.kms.rds_key_arn
  
  tags = local.tags
}

# ElastiCache Redis
module "elasticache" {
  source = "./modules/elasticache"
  
  cluster_id           = "${local.name}-redis"
  node_type           = "cache.r6g.xlarge"
  num_cache_nodes     = 3
  parameter_group_name = "default.redis7"
  
  subnet_group_name  = module.vpc.elasticache_subnet_group_name
  security_group_ids = [module.security_groups.cache_sg_id]
  
  # Clustering
  replication_group_id         = "${local.name}-redis-cluster"
  num_node_groups             = 3
  replicas_per_node_group     = 2
  
  # Backups
  snapshot_retention_limit = 7
  snapshot_window         = "05:00-09:00"
  
  # Encryption
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  auth_token                = var.redis_auth_token
  
  tags = local.tags
}

# S3 Buckets
module "s3" {
  source = "./modules/s3"
  
  environment = var.environment
  
  buckets = {
    raw_data = {
      name_suffix = "raw-data"
      lifecycle_rules = [
        {
          id     = "transition_to_ia"
          status = "Enabled"
          transitions = [
            {
              days          = 30
              storage_class = "STANDARD_IA"
            },
            {
              days          = 90
              storage_class = "GLACIER"
            }
          ]
        }
      ]
    }
    
    processed_data = {
      name_suffix = "processed-data"
      lifecycle_rules = [
        {
          id     = "transition_to_ia"
          status = "Enabled"
          transitions = [
            {
              days          = 60
              storage_class = "STANDARD_IA"
            }
          ]
        }
      ]
    }
    
    ml_models = {
      name_suffix = "ml-models"
      versioning  = true
    }
    
    backups = {
      name_suffix = "backups"
      replication = {
        destination_bucket = "kopitar-backups-dr"
        destination_region = "us-west-2"
      }
    }
  }
  
  tags = local.tags
}

# Security Groups
module "security_groups" {
  source = "./modules/security-groups"
  
  name   = local.name
  vpc_id = module.vpc.vpc_id
  
  tags = local.tags
}

# IAM Roles and Policies
module "iam" {
  source = "./modules/iam"
  
  name             = local.name
  eks_cluster_name = module.eks.cluster_name
  
  tags = local.tags
}

# KMS Keys
module "kms" {
  source = "./modules/kms"
  
  name = local.name
  
  tags = local.tags
}

# Application Load Balancer
module "alb" {
  source = "./modules/alb"
  
  name = "${local.name}-alb"
  
  vpc_id          = module.vpc.vpc_id
  subnets         = module.vpc.public_subnets
  security_groups = [module.security_groups.alb_sg_id]
  
  # SSL Certificate
  certificate_arn = module.acm.certificate_arn
  
  tags = local.tags
}

# ACM Certificate
module "acm" {
  source = "./modules/acm"
  
  domain_name = var.domain_name
  zone_id     = var.route53_zone_id
  
  tags = local.tags
}

# CloudFront Distribution
module "cloudfront" {
  source = "./modules/cloudfront"
  
  domain_name = var.domain_name
  alb_domain  = module.alb.dns_name
  
  # S3 bucket for static assets
  s3_bucket_domain = module.s3.buckets["processed_data"].bucket_domain_name
  
  # WAF
  web_acl_id = module.waf.web_acl_arn
  
  # SSL Certificate
  certificate_arn = module.acm.cloudfront_certificate_arn
  
  tags = local.tags
}

# AWS WAF
module "waf" {
  source = "./modules/waf"
  
  name = "${local.name}-waf"
  
  # Rate limiting
  rate_limit = 2000  # requests per 5 minutes
  
  tags = local.tags
}

# TimeStream Database
module "timestream" {
  source = "./modules/timestream"
  
  database_name = "${local.name}-metrics"
  
  tables = {
    player_performance = {
      memory_store_retention_period_in_hours  = 24
      magnetic_store_retention_period_in_days = 730  # 2 years
    }
    
    system_metrics = {
      memory_store_retention_period_in_hours  = 6
      magnetic_store_retention_period_in_days = 30
    }
  }
  
  tags = local.tags
}

# EMR Cluster for Spark Processing
module "emr" {
  source = "./modules/emr"
  
  name = "${local.name}-emr"
  
  release_label = "emr-6.14.0"
  applications  = ["Spark", "Hadoop", "Hive"]
  
  # Instance configuration
  master_instance_type = "m5.xlarge"
  core_instance_type   = "m5.2xlarge"
  core_instance_count  = 3
  
  # Auto scaling
  core_instance_count_min = 3
  core_instance_count_max = 10
  
  # Networking
  subnet_id              = module.vpc.private_subnets[0]
  additional_security_groups = [module.security_groups.emr_sg_id]
  
  # S3 logging
  log_uri = "s3://${module.s3.buckets["raw_data"].id}/emr-logs/"
  
  tags = local.tags
}

# Managed Airflow (MWAA)
module "airflow" {
  source = "./modules/airflow"
  
  name = "${local.name}-airflow"
  
  # Environment configuration
  environment_class                = "mw1.large"
  min_workers                      = 2
  max_workers                      = 10
  
  # Networking
  subnet_ids         = module.vpc.private_subnets
  security_group_ids = [module.security_groups.airflow_sg_id]
  
  # S3 configuration
  source_bucket_arn = module.s3.buckets["processed_data"].arn
  
  # Execution role
  execution_role_arn = module.iam.airflow_execution_role_arn
  
  tags = local.tags
}

# SageMaker for ML
module "sagemaker" {
  source = "./modules/sagemaker"
  
  name = local.name
  
  # Notebook instance for development
  notebook_instance_type = "ml.t3.medium"
  
  # Model endpoints
  endpoints = {
    fatigue_predictor = {
      instance_type = "ml.m5.xlarge"
      instance_count = 2
      auto_scaling = {
        min_capacity = 2
        max_capacity = 5
      }
    }
    
    performance_predictor = {
      instance_type = "ml.m5.xlarge"
      instance_count = 2
      auto_scaling = {
        min_capacity = 2
        max_capacity = 5
      }
    }
  }
  
  # IAM role
  execution_role_arn = module.iam.sagemaker_execution_role_arn
  
  # Networking
  subnet_ids         = module.vpc.private_subnets
  security_group_ids = [module.security_groups.sagemaker_sg_id]
  
  tags = local.tags
}

# OpenSearch for logging
module "opensearch" {
  source = "./modules/opensearch"
  
  domain_name = "${local.name}-logs"
  
  # Instance configuration
  instance_type  = "r5.large.search"
  instance_count = 3
  
  # Storage
  volume_type = "gp3"
  volume_size = 500
  
  # Networking
  subnet_ids         = module.vpc.private_subnets
  security_group_ids = [module.security_groups.opensearch_sg_id]
  
  tags = local.tags
}

# CloudWatch Dashboards and Alarms
module "monitoring" {
  source = "./modules/monitoring"
  
  name = local.name
  
  # Resources to monitor
  eks_cluster_name = module.eks.cluster_name
  rds_instance_id  = module.rds.instance_id
  alb_arn_suffix   = module.alb.arn_suffix
  
  # Notification
  sns_topic_arn = module.sns.alert_topic_arn
  
  tags = local.tags
}

# SNS for alerts
module "sns" {
  source = "./modules/sns"
  
  name = local.name
  
  # Email subscriptions
  email_endpoints = var.alert_email_addresses
  
  tags = local.tags
}