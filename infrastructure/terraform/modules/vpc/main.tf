# VPC Module for Kopitar Platform
# Creates a production-ready VPC with public, private, and database subnets

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

# Main VPC
resource "aws_vpc" "main" {
  cidr_block           = var.cidr
  enable_dns_hostnames = var.enable_dns_hostnames
  enable_dns_support   = var.enable_dns_support
  
  tags = merge(
    var.tags,
    {
      Name = var.name
      Type = "main-vpc"
    }
  )
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  
  tags = merge(
    var.tags,
    {
      Name = "${var.name}-igw"
    }
  )
}

# Public Subnets
resource "aws_subnet" "public" {
  count = length(var.public_subnets)
  
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnets[count.index]
  availability_zone       = var.azs[count.index]
  map_public_ip_on_launch = true
  
  tags = merge(
    var.tags,
    {
      Name = "${var.name}-public-${var.azs[count.index]}"
      Type = "public"
      "kubernetes.io/role/elb" = "1"
    }
  )
}

# Private Subnets
resource "aws_subnet" "private" {
  count = length(var.private_subnets)
  
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.private_subnets[count.index]
  availability_zone = var.azs[count.index]
  
  tags = merge(
    var.tags,
    {
      Name = "${var.name}-private-${var.azs[count.index]}"
      Type = "private"
      "kubernetes.io/role/internal-elb" = "1"
    }
  )
}

# Database Subnets
resource "aws_subnet" "database" {
  count = length(var.database_subnets)
  
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.database_subnets[count.index]
  availability_zone = var.azs[count.index]
  
  tags = merge(
    var.tags,
    {
      Name = "${var.name}-database-${var.azs[count.index]}"
      Type = "database"
    }
  )
}

# Elastic IPs for NAT Gateways
resource "aws_eip" "nat" {
  count = var.enable_nat_gateway ? length(var.public_subnets) : 0
  
  domain = "vpc"
  
  depends_on = [aws_internet_gateway.main]
  
  tags = merge(
    var.tags,
    {
      Name = "${var.name}-nat-eip-${count.index + 1}"
    }
  )
}

# NAT Gateways
resource "aws_nat_gateway" "main" {
  count = var.enable_nat_gateway ? length(var.public_subnets) : 0
  
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id
  
  depends_on = [aws_internet_gateway.main]
  
  tags = merge(
    var.tags,
    {
      Name = "${var.name}-nat-${var.azs[count.index]}"
    }
  )
}

# Route Tables - Public
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }
  
  tags = merge(
    var.tags,
    {
      Name = "${var.name}-public-rt"
    }
  )
}

# Route Tables - Private
resource "aws_route_table" "private" {
  count = var.enable_nat_gateway ? length(var.private_subnets) : 1
  
  vpc_id = aws_vpc.main.id
  
  dynamic "route" {
    for_each = var.enable_nat_gateway ? [1] : []
    content {
      cidr_block     = "0.0.0.0/0"
      nat_gateway_id = aws_nat_gateway.main[count.index].id
    }
  }
  
  tags = merge(
    var.tags,
    {
      Name = "${var.name}-private-rt-${count.index + 1}"
    }
  )
}

# Route Tables - Database
resource "aws_route_table" "database" {
  count = length(var.database_subnets) > 0 ? 1 : 0
  
  vpc_id = aws_vpc.main.id
  
  tags = merge(
    var.tags,
    {
      Name = "${var.name}-database-rt"
    }
  )
}

# Route Table Associations - Public
resource "aws_route_table_association" "public" {
  count = length(var.public_subnets)
  
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# Route Table Associations - Private
resource "aws_route_table_association" "private" {
  count = length(var.private_subnets)
  
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[var.enable_nat_gateway ? count.index : 0].id
}

# Route Table Associations - Database
resource "aws_route_table_association" "database" {
  count = length(var.database_subnets)
  
  subnet_id      = aws_subnet.database[count.index].id
  route_table_id = aws_route_table.database[0].id
}

# Database Subnet Group
resource "aws_db_subnet_group" "database" {
  count = length(var.database_subnets) > 0 ? 1 : 0
  
  name       = "${var.name}-db-subnet-group"
  subnet_ids = aws_subnet.database[*].id
  
  tags = merge(
    var.tags,
    {
      Name = "${var.name}-db-subnet-group"
    }
  )
}

# ElastiCache Subnet Group
resource "aws_elasticache_subnet_group" "main" {
  count = length(var.database_subnets) > 0 ? 1 : 0
  
  name       = "${var.name}-cache-subnet-group"
  subnet_ids = aws_subnet.database[*].id
  
  tags = merge(
    var.tags,
    {
      Name = "${var.name}-cache-subnet-group"
    }
  )
}

# VPC Flow Logs
resource "aws_flow_log" "vpc" {
  count = var.enable_flow_log ? 1 : 0
  
  iam_role_arn    = var.create_flow_log_cloudwatch_iam_role ? aws_iam_role.flow_log[0].arn : var.flow_log_cloudwatch_iam_role_arn
  log_destination = var.create_flow_log_cloudwatch_log_group ? aws_cloudwatch_log_group.flow_log[0].arn : var.flow_log_cloudwatch_log_group_arn
  traffic_type    = "ALL"
  vpc_id          = aws_vpc.main.id
  
  tags = merge(
    var.tags,
    {
      Name = "${var.name}-vpc-flow-log"
    }
  )
}

# CloudWatch Log Group for VPC Flow Logs
resource "aws_cloudwatch_log_group" "flow_log" {
  count = var.enable_flow_log && var.create_flow_log_cloudwatch_log_group ? 1 : 0
  
  name              = "/aws/vpc/${var.name}-flow-log"
  retention_in_days = var.flow_log_cloudwatch_log_group_retention_in_days
  kms_key_id        = var.flow_log_cloudwatch_log_group_kms_key_id
  
  tags = merge(
    var.tags,
    {
      Name = "${var.name}-vpc-flow-log-group"
    }
  )
}

# IAM Role for VPC Flow Logs
resource "aws_iam_role" "flow_log" {
  count = var.enable_flow_log && var.create_flow_log_cloudwatch_iam_role ? 1 : 0
  
  name_prefix = "${var.name}-flow-log-"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "vpc-flow-logs.amazonaws.com"
        }
      }
    ]
  })
  
  tags = var.tags
}

# IAM Role Policy for VPC Flow Logs
resource "aws_iam_role_policy" "flow_log" {
  count = var.enable_flow_log && var.create_flow_log_cloudwatch_iam_role ? 1 : 0
  
  name_prefix = "${var.name}-flow-log-"
  role        = aws_iam_role.flow_log[0].id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams"
        ]
        Effect   = "Allow"
        Resource = "*"
      }
    ]
  })
}

# VPC Endpoints for AWS Services
resource "aws_vpc_endpoint" "s3" {
  count = var.enable_s3_endpoint ? 1 : 0
  
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.${var.region}.s3"
  vpc_endpoint_type = "Gateway"
  
  route_table_ids = concat(
    [aws_route_table.public.id],
    aws_route_table.private[*].id,
    aws_route_table.database[*].id
  )
  
  tags = merge(
    var.tags,
    {
      Name = "${var.name}-s3-endpoint"
    }
  )
}

resource "aws_vpc_endpoint" "ec2" {
  count = var.enable_ec2_endpoint ? 1 : 0
  
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.region}.ec2"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoint[0].id]
  
  private_dns_enabled = true
  
  tags = merge(
    var.tags,
    {
      Name = "${var.name}-ec2-endpoint"
    }
  )
}

resource "aws_vpc_endpoint" "ecr_dkr" {
  count = var.enable_ecr_endpoint ? 1 : 0
  
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.region}.ecr.dkr"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoint[0].id]
  
  private_dns_enabled = true
  
  tags = merge(
    var.tags,
    {
      Name = "${var.name}-ecr-dkr-endpoint"
    }
  )
}

resource "aws_vpc_endpoint" "ecr_api" {
  count = var.enable_ecr_endpoint ? 1 : 0
  
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.region}.ecr.api"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoint[0].id]
  
  private_dns_enabled = true
  
  tags = merge(
    var.tags,
    {
      Name = "${var.name}-ecr-api-endpoint"
    }
  )
}

# Security Group for VPC Endpoints
resource "aws_security_group" "vpc_endpoint" {
  count = (var.enable_ec2_endpoint || var.enable_ecr_endpoint) ? 1 : 0
  
  name_prefix = "${var.name}-vpc-endpoint-"
  vpc_id      = aws_vpc.main.id
  
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [var.cidr]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = merge(
    var.tags,
    {
      Name = "${var.name}-vpc-endpoint-sg"
    }
  )
}