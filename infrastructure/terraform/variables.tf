# Kopitar Infrastructure - Terraform Variables

# General Configuration
variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "kopitar"
}

# Networking
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b", "us-east-1c"]
}

# Database Configuration
variable "db_username" {
  description = "Username for RDS PostgreSQL"
  type        = string
  default     = "postgres"
  sensitive   = true
}

variable "db_password" {
  description = "Password for RDS PostgreSQL"
  type        = string
  sensitive   = true
}

variable "db_instance_class" {
  description = "Instance class for RDS"
  type        = string
  default     = "db.r6g.2xlarge"
}

variable "db_allocated_storage" {
  description = "Allocated storage for RDS (GB)"
  type        = number
  default     = 1000
}

variable "db_backup_retention_period" {
  description = "Backup retention period for RDS (days)"
  type        = number
  default     = 30
}

# ElastiCache Configuration
variable "redis_node_type" {
  description = "Node type for ElastiCache Redis"
  type        = string
  default     = "cache.r6g.xlarge"
}

variable "redis_num_cache_nodes" {
  description = "Number of cache nodes for Redis"
  type        = number
  default     = 3
}

variable "redis_auth_token" {
  description = "Auth token for Redis"
  type        = string
  sensitive   = true
}

# EKS Configuration
variable "cluster_version" {
  description = "Kubernetes version for EKS cluster"
  type        = string
  default     = "1.28"
}

variable "node_groups" {
  description = "EKS node group configurations"
  type = map(object({
    instance_types = list(string)
    min_size       = number
    max_size       = number
    desired_size   = number
    disk_size      = number
    labels         = map(string)
    taints         = list(object({
      key    = string
      value  = string
      effect = string
    }))
  }))
  
  default = {
    api_nodes = {
      instance_types = ["t3.large"]
      min_size       = 3
      max_size       = 20
      desired_size   = 6
      disk_size      = 50
      labels = {
        workload = "api"
      }
      taints = []
    }
    
    worker_nodes = {
      instance_types = ["c5.2xlarge"]
      min_size       = 2
      max_size       = 10
      desired_size   = 4
      disk_size      = 100
      labels = {
        workload = "worker"
      }
      taints = []
    }
    
    streaming_nodes = {
      instance_types = ["m5.xlarge"]
      min_size       = 2
      max_size       = 8
      desired_size   = 3
      disk_size      = 50
      labels = {
        workload = "streaming"
      }
      taints = []
    }
  }
}

# Domain and SSL
variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = "api.kopitar-analytics.com"
}

variable "route53_zone_id" {
  description = "Route53 hosted zone ID"
  type        = string
}

# Monitoring and Alerting
variable "alert_email_addresses" {
  description = "Email addresses for alerts"
  type        = list(string)
  default     = ["admin@kopitar-analytics.com"]
}

variable "enable_detailed_monitoring" {
  description = "Enable detailed CloudWatch monitoring"
  type        = bool
  default     = true
}

# S3 Configuration
variable "s3_buckets" {
  description = "S3 bucket configurations"
  type = map(object({
    versioning_enabled = bool
    lifecycle_rules = list(object({
      id     = string
      status = string
      transitions = list(object({
        days          = number
        storage_class = string
      }))
    }))
    cross_region_replication = object({
      enabled            = bool
      destination_bucket = string
      destination_region = string
    })
  }))
  
  default = {
    raw_data = {
      versioning_enabled = false
      lifecycle_rules = [
        {
          id     = "transition_lifecycle"
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
      cross_region_replication = {
        enabled            = false
        destination_bucket = ""
        destination_region = ""
      }
    }
    
    processed_data = {
      versioning_enabled = false
      lifecycle_rules = [
        {
          id     = "transition_lifecycle"
          status = "Enabled"
          transitions = [
            {
              days          = 60
              storage_class = "STANDARD_IA"
            }
          ]
        }
      ]
      cross_region_replication = {
        enabled            = false
        destination_bucket = ""
        destination_region = ""
      }
    }
    
    ml_models = {
      versioning_enabled = true
      lifecycle_rules    = []
      cross_region_replication = {
        enabled            = false
        destination_bucket = ""
        destination_region = ""
      }
    }
    
    backups = {
      versioning_enabled = true
      lifecycle_rules    = []
      cross_region_replication = {
        enabled            = true
        destination_bucket = "kopitar-backups-dr"
        destination_region = "us-west-2"
      }
    }
  }
}

# EMR Configuration
variable "emr_release_label" {
  description = "EMR release label"
  type        = string
  default     = "emr-6.14.0"
}

variable "emr_master_instance_type" {
  description = "Instance type for EMR master node"
  type        = string
  default     = "m5.xlarge"
}

variable "emr_core_instance_type" {
  description = "Instance type for EMR core nodes"
  type        = string
  default     = "m5.2xlarge"
}

variable "emr_core_instance_count" {
  description = "Number of EMR core instances"
  type        = number
  default     = 3
}

# SageMaker Configuration
variable "sagemaker_notebook_instance_type" {
  description = "Instance type for SageMaker notebook"
  type        = string
  default     = "ml.t3.medium"
}

variable "sagemaker_endpoints" {
  description = "SageMaker endpoint configurations"
  type = map(object({
    instance_type  = string
    instance_count = number
    auto_scaling = object({
      min_capacity = number
      max_capacity = number
    })
  }))
  
  default = {
    fatigue_predictor = {
      instance_type  = "ml.m5.xlarge"
      instance_count = 2
      auto_scaling = {
        min_capacity = 2
        max_capacity = 5
      }
    }
    
    performance_predictor = {
      instance_type  = "ml.m5.xlarge"
      instance_count = 2
      auto_scaling = {
        min_capacity = 2
        max_capacity = 5
      }
    }
  }
}

# MWAA (Airflow) Configuration
variable "airflow_environment_class" {
  description = "Environment class for MWAA"
  type        = string
  default     = "mw1.large"
  
  validation {
    condition     = contains(["mw1.small", "mw1.medium", "mw1.large"], var.airflow_environment_class)
    error_message = "Airflow environment class must be mw1.small, mw1.medium, or mw1.large."
  }
}

variable "airflow_min_workers" {
  description = "Minimum number of Airflow workers"
  type        = number
  default     = 2
}

variable "airflow_max_workers" {
  description = "Maximum number of Airflow workers"
  type        = number
  default     = 10
}

# OpenSearch Configuration
variable "opensearch_instance_type" {
  description = "Instance type for OpenSearch"
  type        = string
  default     = "r5.large.search"
}

variable "opensearch_instance_count" {
  description = "Number of OpenSearch instances"
  type        = number
  default     = 3
}

variable "opensearch_volume_size" {
  description = "Volume size for OpenSearch instances (GB)"
  type        = number
  default     = 500
}

# TimeStream Configuration
variable "timestream_memory_retention_hours" {
  description = "Memory retention period for TimeStream (hours)"
  type        = number
  default     = 24
}

variable "timestream_magnetic_retention_days" {
  description = "Magnetic retention period for TimeStream (days)"
  type        = number
  default     = 730  # 2 years
}

# WAF Configuration
variable "waf_rate_limit" {
  description = "Rate limit for WAF (requests per 5 minutes)"
  type        = number
  default     = 2000
}

variable "waf_enable_geo_blocking" {
  description = "Enable geographic blocking in WAF"
  type        = bool
  default     = false
}

variable "waf_blocked_countries" {
  description = "List of country codes to block"
  type        = list(string)
  default     = []
}

# Cost Optimization
variable "enable_spot_instances" {
  description = "Enable spot instances for cost optimization"
  type        = bool
  default     = true
}

variable "spot_instance_types" {
  description = "Instance types to use for spot instances"
  type        = list(string)
  default     = ["m5.large", "m5a.large", "m4.large"]
}

# Backup Configuration
variable "backup_retention_days" {
  description = "Number of days to retain backups"
  type        = number
  default     = 30
}

variable "enable_cross_region_backup" {
  description = "Enable cross-region backup replication"
  type        = bool
  default     = true
}

variable "backup_region" {
  description = "Region for backup replication"
  type        = string
  default     = "us-west-2"
}

# Security Configuration
variable "enable_encryption" {
  description = "Enable encryption at rest and in transit"
  type        = bool
  default     = true
}

variable "kms_key_deletion_window" {
  description = "KMS key deletion window in days"
  type        = number
  default     = 7
}

variable "enable_vpc_flow_logs" {
  description = "Enable VPC flow logs"
  type        = bool
  default     = true
}

# Feature Flags
variable "enable_dev_tools" {
  description = "Enable development tools and debugging"
  type        = bool
  default     = false
}

variable "enable_experimental_features" {
  description = "Enable experimental features"
  type        = bool
  default     = false
}

# Resource Tagging
variable "additional_tags" {
  description = "Additional tags to apply to resources"
  type        = map(string)
  default     = {}
}