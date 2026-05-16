# VPC Module Outputs

output "vpc_id" {
  description = "The ID of the VPC"
  value       = aws_vpc.main.id
}

output "vpc_arn" {
  description = "The ARN of the VPC"
  value       = aws_vpc.main.arn
}

output "vpc_cidr_block" {
  description = "The CIDR block of the VPC"
  value       = aws_vpc.main.cidr_block
}

output "vpc_instance_tenancy" {
  description = "Tenancy of instances spin up within VPC"
  value       = aws_vpc.main.instance_tenancy
}

output "vpc_enable_dns_support" {
  description = "Whether or not the VPC has DNS support"
  value       = aws_vpc.main.enable_dns_support
}

output "vpc_enable_dns_hostnames" {
  description = "Whether or not the VPC has DNS hostname support"
  value       = aws_vpc.main.enable_dns_hostnames
}

output "vpc_main_route_table_id" {
  description = "The ID of the main route table associated with this VPC"
  value       = aws_vpc.main.main_route_table_id
}

output "vpc_default_security_group_id" {
  description = "The ID of the security group created by default on VPC creation"
  value       = aws_vpc.main.default_security_group_id
}

output "vpc_default_network_acl_id" {
  description = "The ID of the default network ACL"
  value       = aws_vpc.main.default_network_acl_id
}

output "vpc_default_route_table_id" {
  description = "The ID of the default route table"
  value       = aws_vpc.main.default_route_table_id
}

# Internet Gateway
output "igw_id" {
  description = "The ID of the Internet Gateway"
  value       = aws_internet_gateway.main.id
}

output "igw_arn" {
  description = "The ARN of the Internet Gateway"
  value       = aws_internet_gateway.main.arn
}

# Subnets
output "private_subnets" {
  description = "List of IDs of private subnets"
  value       = aws_subnet.private[*].id
}

output "private_subnet_arns" {
  description = "List of ARNs of private subnets"
  value       = aws_subnet.private[*].arn
}

output "private_subnets_cidr_blocks" {
  description = "List of cidr_blocks of private subnets"
  value       = aws_subnet.private[*].cidr_block
}

output "public_subnets" {
  description = "List of IDs of public subnets"
  value       = aws_subnet.public[*].id
}

output "public_subnet_arns" {
  description = "List of ARNs of public subnets"
  value       = aws_subnet.public[*].arn
}

output "public_subnets_cidr_blocks" {
  description = "List of cidr_blocks of public subnets"
  value       = aws_subnet.public[*].cidr_block
}

output "database_subnets" {
  description = "List of IDs of database subnets"
  value       = aws_subnet.database[*].id
}

output "database_subnet_arns" {
  description = "List of ARNs of database subnets"
  value       = aws_subnet.database[*].arn
}

output "database_subnets_cidr_blocks" {
  description = "List of cidr_blocks of database subnets"
  value       = aws_subnet.database[*].cidr_block
}

output "database_subnet_group" {
  description = "ID of database subnet group"
  value       = try(aws_db_subnet_group.database[0].id, null)
}

output "database_subnet_group_name" {
  description = "Name of database subnet group"
  value       = try(aws_db_subnet_group.database[0].name, null)
}

output "elasticache_subnet_group_name" {
  description = "Name of ElastiCache subnet group"
  value       = try(aws_elasticache_subnet_group.main[0].name, null)
}

output "elasticache_subnet_group_id" {
  description = "ID of ElastiCache subnet group"
  value       = try(aws_elasticache_subnet_group.main[0].id, null)
}

# Route Tables
output "private_route_table_ids" {
  description = "List of IDs of the private route tables"
  value       = aws_route_table.private[*].id
}

output "public_route_table_ids" {
  description = "List of IDs of the public route tables"
  value       = [aws_route_table.public.id]
}

output "database_route_table_ids" {
  description = "List of IDs of the database route tables"
  value       = aws_route_table.database[*].id
}

# NAT Gateways
output "nat_ids" {
  description = "List of IDs of the NAT Gateways"
  value       = aws_nat_gateway.main[*].id
}

output "nat_public_ips" {
  description = "List of public Elastic IPs created for AWS NAT Gateway"
  value       = aws_eip.nat[*].public_ip
}

output "natgw_ids" {
  description = "List of IDs of the NAT Gateways"
  value       = aws_nat_gateway.main[*].id
}

# VPC Flow Logs
output "vpc_flow_log_id" {
  description = "The ID of the Flow Log resource"
  value       = try(aws_flow_log.vpc[0].id, null)
}

output "vpc_flow_log_destination_arn" {
  description = "The ARN of the destination for VPC Flow Logs"
  value       = try(aws_flow_log.vpc[0].log_destination, null)
}

output "vpc_flow_log_destination_type" {
  description = "The type of the destination for VPC Flow Logs"
  value       = try(aws_flow_log.vpc[0].log_destination_type, null)
}

output "vpc_flow_log_cloudwatch_iam_role_arn" {
  description = "The ARN of the IAM role used when pushing logs to Cloudwatch log group"
  value       = try(aws_iam_role.flow_log[0].arn, null)
}

# VPC Endpoints
output "vpc_endpoint_s3_id" {
  description = "The ID of VPC endpoint for S3"
  value       = try(aws_vpc_endpoint.s3[0].id, null)
}

output "vpc_endpoint_s3_pl_id" {
  description = "The prefix list for the S3 VPC endpoint"
  value       = try(aws_vpc_endpoint.s3[0].prefix_list_id, null)
}

output "vpc_endpoint_ec2_id" {
  description = "The ID of VPC endpoint for EC2"
  value       = try(aws_vpc_endpoint.ec2[0].id, null)
}

output "vpc_endpoint_ec2_dns_entry" {
  description = "The DNS entries for the VPC Endpoint for EC2"
  value       = try(aws_vpc_endpoint.ec2[0].dns_entry, null)
}

output "vpc_endpoint_ecr_dkr_id" {
  description = "The ID of VPC endpoint for ECR DKR"
  value       = try(aws_vpc_endpoint.ecr_dkr[0].id, null)
}

output "vpc_endpoint_ecr_dkr_dns_entry" {
  description = "The DNS entries for the VPC Endpoint for ECR DKR"
  value       = try(aws_vpc_endpoint.ecr_dkr[0].dns_entry, null)
}

output "vpc_endpoint_ecr_api_id" {
  description = "The ID of VPC endpoint for ECR API"
  value       = try(aws_vpc_endpoint.ecr_api[0].id, null)
}

output "vpc_endpoint_ecr_api_dns_entry" {
  description = "The DNS entries for the VPC Endpoint for ECR API"
  value       = try(aws_vpc_endpoint.ecr_api[0].dns_entry, null)
}

# Availability Zones
output "azs" {
  description = "A list of availability zones specified as argument to this module"
  value       = var.azs
}