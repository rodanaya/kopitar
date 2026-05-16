# Kopitar Infrastructure - Terraform Outputs

# VPC Outputs
output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = module.vpc.vpc_cidr_block
}

output "private_subnets" {
  description = "List of IDs of private subnets"
  value       = module.vpc.private_subnets
}

output "public_subnets" {
  description = "List of IDs of public subnets"
  value       = module.vpc.public_subnets
}

output "database_subnets" {
  description = "List of IDs of database subnets"
  value       = module.vpc.database_subnets
}

# EKS Cluster Outputs
output "cluster_id" {
  description = "EKS cluster ID"
  value       = module.eks.cluster_id
}

output "cluster_arn" {
  description = "EKS cluster ARN"
  value       = module.eks.cluster_arn
}

output "cluster_endpoint" {
  description = "Endpoint for EKS control plane"
  value       = module.eks.cluster_endpoint
}

output "cluster_security_group_id" {
  description = "Security group IDs attached to the EKS cluster"
  value       = module.eks.cluster_security_group_id
}

output "cluster_certificate_authority_data" {
  description = "Base64 encoded certificate data required to communicate with the cluster"
  value       = module.eks.cluster_certificate_authority_data
  sensitive   = true
}

output "cluster_token" {
  description = "Token to use to authenticate with the cluster"
  value       = module.eks.cluster_token
  sensitive   = true
}

output "oidc_provider_arn" {
  description = "The ARN of the OIDC Provider for IRSA"
  value       = module.eks.oidc_provider_arn
}

# RDS Outputs
output "rds_instance_endpoint" {
  description = "RDS instance endpoint"
  value       = module.rds.instance_endpoint
  sensitive   = true
}

output "rds_instance_port" {
  description = "RDS instance port"
  value       = module.rds.instance_port
}

output "rds_instance_id" {
  description = "RDS instance ID"
  value       = module.rds.instance_id
}

output "rds_instance_arn" {
  description = "RDS instance ARN"
  value       = module.rds.instance_arn
}

output "rds_read_replica_endpoint" {
  description = "RDS read replica endpoint"
  value       = module.rds.read_replica_endpoint
  sensitive   = true
}

# ElastiCache Outputs
output "redis_cluster_id" {
  description = "ElastiCache Redis cluster ID"
  value       = module.elasticache.cluster_id
}

output "redis_primary_endpoint" {
  description = "Redis primary endpoint"
  value       = module.elasticache.primary_endpoint
  sensitive   = true
}

output "redis_configuration_endpoint" {
  description = "Redis configuration endpoint"
  value       = module.elasticache.configuration_endpoint
  sensitive   = true
}

output "redis_port" {
  description = "Redis port"
  value       = module.elasticache.port
}

# S3 Bucket Outputs
output "s3_bucket_raw_data" {
  description = "S3 bucket for raw data"
  value = {
    id                  = module.s3.buckets["raw_data"].id
    arn                 = module.s3.buckets["raw_data"].arn
    bucket_domain_name  = module.s3.buckets["raw_data"].bucket_domain_name
  }
}

output "s3_bucket_processed_data" {
  description = "S3 bucket for processed data"
  value = {
    id                  = module.s3.buckets["processed_data"].id
    arn                 = module.s3.buckets["processed_data"].arn
    bucket_domain_name  = module.s3.buckets["processed_data"].bucket_domain_name
  }
}

output "s3_bucket_ml_models" {
  description = "S3 bucket for ML models"
  value = {
    id                  = module.s3.buckets["ml_models"].id
    arn                 = module.s3.buckets["ml_models"].arn
    bucket_domain_name  = module.s3.buckets["ml_models"].bucket_domain_name
  }
}

output "s3_bucket_backups" {
  description = "S3 bucket for backups"
  value = {
    id                  = module.s3.buckets["backups"].id
    arn                 = module.s3.buckets["backups"].arn
    bucket_domain_name  = module.s3.buckets["backups"].bucket_domain_name
  }
}

# Load Balancer Outputs
output "alb_dns_name" {
  description = "DNS name of the load balancer"
  value       = module.alb.dns_name
}

output "alb_arn" {
  description = "ARN of the load balancer"
  value       = module.alb.arn
}

output "alb_zone_id" {
  description = "Zone ID of the load balancer"
  value       = module.alb.zone_id
}

# CloudFront Outputs
output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  value       = module.cloudfront.distribution_id
}

output "cloudfront_domain_name" {
  description = "CloudFront distribution domain name"
  value       = module.cloudfront.domain_name
}

output "cloudfront_hosted_zone_id" {
  description = "CloudFront distribution hosted zone ID"
  value       = module.cloudfront.hosted_zone_id
}

# ACM Certificate Outputs
output "acm_certificate_arn" {
  description = "ACM certificate ARN"
  value       = module.acm.certificate_arn
}

output "acm_cloudfront_certificate_arn" {
  description = "ACM certificate ARN for CloudFront"
  value       = module.acm.cloudfront_certificate_arn
}

# WAF Outputs
output "waf_web_acl_arn" {
  description = "WAF Web ACL ARN"
  value       = module.waf.web_acl_arn
}

output "waf_web_acl_id" {
  description = "WAF Web ACL ID"
  value       = module.waf.web_acl_id
}

# TimeStream Outputs
output "timestream_database_name" {
  description = "TimeStream database name"
  value       = module.timestream.database_name
}

output "timestream_database_arn" {
  description = "TimeStream database ARN"
  value       = module.timestream.database_arn
}

output "timestream_table_arns" {
  description = "TimeStream table ARNs"
  value       = module.timestream.table_arns
}

# EMR Outputs
output "emr_cluster_id" {
  description = "EMR cluster ID"
  value       = module.emr.cluster_id
}

output "emr_master_public_dns" {
  description = "EMR master node public DNS"
  value       = module.emr.master_public_dns
  sensitive   = true
}

# Airflow Outputs
output "airflow_environment_arn" {
  description = "MWAA environment ARN"
  value       = module.airflow.environment_arn
}

output "airflow_webserver_url" {
  description = "Airflow webserver URL"
  value       = module.airflow.webserver_url
  sensitive   = true
}

# SageMaker Outputs
output "sagemaker_notebook_instance_name" {
  description = "SageMaker notebook instance name"
  value       = module.sagemaker.notebook_instance_name
}

output "sagemaker_notebook_instance_url" {
  description = "SageMaker notebook instance URL"
  value       = module.sagemaker.notebook_instance_url
  sensitive   = true
}

output "sagemaker_endpoint_urls" {
  description = "SageMaker endpoint URLs"
  value       = module.sagemaker.endpoint_urls
  sensitive   = true
}

# OpenSearch Outputs
output "opensearch_domain_endpoint" {
  description = "OpenSearch domain endpoint"
  value       = module.opensearch.domain_endpoint
  sensitive   = true
}

output "opensearch_domain_arn" {
  description = "OpenSearch domain ARN"
  value       = module.opensearch.domain_arn
}

output "opensearch_kibana_endpoint" {
  description = "OpenSearch Kibana endpoint"
  value       = module.opensearch.kibana_endpoint
  sensitive   = true
}

# IAM Role Outputs
output "eks_node_group_role_arn" {
  description = "EKS node group IAM role ARN"
  value       = module.iam.eks_node_group_role_arn
}

output "airflow_execution_role_arn" {
  description = "Airflow execution role ARN"
  value       = module.iam.airflow_execution_role_arn
}

output "sagemaker_execution_role_arn" {
  description = "SageMaker execution role ARN"
  value       = module.iam.sagemaker_execution_role_arn
}

output "emr_service_role_arn" {
  description = "EMR service role ARN"
  value       = module.iam.emr_service_role_arn
}

# KMS Key Outputs
output "kms_key_rds_arn" {
  description = "KMS key ARN for RDS encryption"
  value       = module.kms.rds_key_arn
}

output "kms_key_s3_arn" {
  description = "KMS key ARN for S3 encryption"
  value       = module.kms.s3_key_arn
}

output "kms_key_eks_arn" {
  description = "KMS key ARN for EKS encryption"
  value       = module.kms.eks_key_arn
}

# Security Group Outputs
output "security_group_ids" {
  description = "Map of security group IDs"
  value = {
    alb_sg_id        = module.security_groups.alb_sg_id
    api_sg_id        = module.security_groups.api_sg_id
    database_sg_id   = module.security_groups.database_sg_id
    cache_sg_id      = module.security_groups.cache_sg_id
    emr_sg_id        = module.security_groups.emr_sg_id
    airflow_sg_id    = module.security_groups.airflow_sg_id
    sagemaker_sg_id  = module.security_groups.sagemaker_sg_id
    opensearch_sg_id = module.security_groups.opensearch_sg_id
  }
}

# Monitoring Outputs
output "cloudwatch_dashboard_url" {
  description = "CloudWatch dashboard URL"
  value       = module.monitoring.dashboard_url
}

output "sns_topic_arn" {
  description = "SNS topic ARN for alerts"
  value       = module.sns.alert_topic_arn
}

# Connection Information for Applications
output "database_connection_info" {
  description = "Database connection information"
  value = {
    host     = module.rds.instance_endpoint
    port     = module.rds.instance_port
    database = "kopitar"
    username = var.db_username
  }
  sensitive = true
}

output "redis_connection_info" {
  description = "Redis connection information"
  value = {
    endpoint = module.elasticache.primary_endpoint
    port     = module.elasticache.port
  }
  sensitive = true
}

# Application URLs
output "application_urls" {
  description = "Application URLs"
  value = {
    api_url         = "https://${var.domain_name}"
    airflow_url     = module.airflow.webserver_url
    sagemaker_url   = module.sagemaker.notebook_instance_url
    opensearch_url  = "https://${module.opensearch.domain_endpoint}"
    monitoring_url  = module.monitoring.dashboard_url
  }
  sensitive = true
}

# Resource Summary
output "resource_summary" {
  description = "Summary of deployed resources"
  value = {
    vpc_id              = module.vpc.vpc_id
    eks_cluster_name    = module.eks.cluster_name
    rds_instance_id     = module.rds.instance_id
    redis_cluster_id    = module.elasticache.cluster_id
    s3_buckets          = keys(module.s3.buckets)
    emr_cluster_id      = module.emr.cluster_id
    airflow_environment = module.airflow.environment_name
    total_resources     = "Deployed successfully"
  }
}

# Cost Estimation
output "estimated_monthly_cost" {
  description = "Estimated monthly cost breakdown (USD)"
  value = {
    compute_eks     = "~800"
    compute_emr     = "~300"
    compute_sagemaker = "~400"
    storage_rds     = "~600"
    storage_s3      = "~200"
    cache_redis     = "~400"
    network_alb_cf  = "~450"
    airflow_mwaa    = "~300"
    monitoring      = "~200"
    other           = "~100"
    total_estimated = "~3750"
    note           = "Costs vary based on usage and reserved instances"
  }
}