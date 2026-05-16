#!/bin/bash

# Kopitar NHL Analytics Platform - Deployment Script
# Automated deployment script for AWS infrastructure and application

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_DIR="${SCRIPT_DIR}/infrastructure/terraform"
K8S_DIR="${SCRIPT_DIR}/infrastructure/kubernetes"
ENVIRONMENT="${ENVIRONMENT:-prod}"
AWS_REGION="${AWS_REGION:-us-east-1}"
CLUSTER_NAME="kopitar-${ENVIRONMENT}-cluster"

# Functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

check_dependencies() {
    log "Checking dependencies..."
    
    local deps=("terraform" "aws" "kubectl" "helm" "docker")
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            error "$dep is required but not installed"
        fi
    done
    
    # Check AWS CLI configuration
    if ! aws sts get-caller-identity &> /dev/null; then
        error "AWS CLI is not configured. Run 'aws configure' first"
    fi
    
    success "All dependencies satisfied"
}

validate_environment() {
    log "Validating environment variables..."
    
    local required_vars=("DB_PASSWORD" "REDIS_AUTH_TOKEN" "JWT_SECRET_KEY" "SECRET_KEY")
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            error "Environment variable $var is required"
        fi
    done
    
    success "Environment validation passed"
}

setup_terraform_backend() {
    log "Setting up Terraform backend..."
    
    # Create S3 bucket for Terraform state
    local bucket_name="kopitar-terraform-state-${ENVIRONMENT}"
    local table_name="kopitar-terraform-lock-${ENVIRONMENT}"
    
    if ! aws s3 ls "s3://${bucket_name}" &> /dev/null; then
        log "Creating S3 bucket for Terraform state..."
        aws s3 mb "s3://${bucket_name}" --region "${AWS_REGION}"
        aws s3api put-bucket-versioning \
            --bucket "${bucket_name}" \
            --versioning-configuration Status=Enabled
        aws s3api put-bucket-encryption \
            --bucket "${bucket_name}" \
            --server-side-encryption-configuration '{
                "Rules": [{
                    "ApplyServerSideEncryptionByDefault": {
                        "SSEAlgorithm": "AES256"
                    }
                }]
            }'
    fi
    
    # Create DynamoDB table for state locking
    if ! aws dynamodb describe-table --table-name "${table_name}" &> /dev/null; then
        log "Creating DynamoDB table for Terraform state locking..."
        aws dynamodb create-table \
            --table-name "${table_name}" \
            --attribute-definitions AttributeName=LockID,AttributeType=S \
            --key-schema AttributeName=LockID,KeyType=HASH \
            --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
            --region "${AWS_REGION}"
        
        # Wait for table to be created
        aws dynamodb wait table-exists --table-name "${table_name}" --region "${AWS_REGION}"
    fi
    
    success "Terraform backend configured"
}

deploy_infrastructure() {
    log "Deploying infrastructure with Terraform..."
    
    cd "${TERRAFORM_DIR}"
    
    # Initialize Terraform
    terraform init
    
    # Validate configuration
    terraform validate
    
    # Plan deployment
    terraform plan \
        -var="environment=${ENVIRONMENT}" \
        -var="aws_region=${AWS_REGION}" \
        -var="db_password=${DB_PASSWORD}" \
        -var="redis_auth_token=${REDIS_AUTH_TOKEN}" \
        -out=tfplan
    
    # Apply if approved
    if [[ "${AUTO_APPROVE:-false}" == "true" ]]; then
        terraform apply -auto-approve tfplan
    else
        echo
        read -p "Do you want to apply these changes? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            terraform apply tfplan
        else
            warning "Deployment cancelled by user"
            exit 0
        fi
    fi
    
    # Save outputs
    terraform output -json > "${SCRIPT_DIR}/terraform-outputs.json"
    
    success "Infrastructure deployed successfully"
    cd "${SCRIPT_DIR}"
}

configure_kubectl() {
    log "Configuring kubectl for EKS cluster..."
    
    aws eks update-kubeconfig \
        --region "${AWS_REGION}" \
        --name "${CLUSTER_NAME}"
    
    # Test connection
    kubectl get nodes
    
    success "kubectl configured for EKS cluster"
}

install_cluster_components() {
    log "Installing cluster components..."
    
    # Install AWS Load Balancer Controller
    log "Installing AWS Load Balancer Controller..."
    helm repo add eks https://aws.github.io/eks-charts
    helm repo update
    
    kubectl apply -k "github.com/aws/eks-charts/stable/aws-load-balancer-controller//crds?ref=master"
    
    helm upgrade --install aws-load-balancer-controller eks/aws-load-balancer-controller \
        -n kube-system \
        --set clusterName="${CLUSTER_NAME}" \
        --set serviceAccount.create=false \
        --set serviceAccount.name=aws-load-balancer-controller \
        --wait
    
    # Install Cluster Autoscaler
    log "Installing Cluster Autoscaler..."
    helm repo add autoscaler https://kubernetes.github.io/autoscaler
    helm upgrade --install cluster-autoscaler autoscaler/cluster-autoscaler \
        -n kube-system \
        --set autoDiscovery.clusterName="${CLUSTER_NAME}" \
        --set awsRegion="${AWS_REGION}" \
        --wait
    
    # Install Prometheus and Grafana
    log "Installing monitoring stack..."
    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
    helm upgrade --install prometheus prometheus-community/kube-prometheus-stack \
        -n monitoring \
        --create-namespace \
        --set grafana.adminPassword="${GRAFANA_PASSWORD:-admin}" \
        --wait
    
    # Install NGINX Ingress Controller
    log "Installing NGINX Ingress Controller..."
    helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
    helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx \
        -n ingress-nginx \
        --create-namespace \
        --wait
    
    success "Cluster components installed"
}

deploy_application() {
    log "Deploying Kopitar application..."
    
    # Create namespace
    kubectl apply -f "${K8S_DIR}/api-deployment.yaml"
    
    # Wait for deployment to be ready
    kubectl wait --for=condition=available --timeout=300s deployment/kopitar-api -n kopitar
    
    # Get service URL
    local service_url
    service_url=$(kubectl get ingress kopitar-api -n kopitar -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
    
    success "Application deployed successfully"
    success "API URL: https://${service_url}"
}

run_health_checks() {
    log "Running health checks..."
    
    # Check API health
    local api_url
    api_url=$(kubectl get ingress kopitar-api -n kopitar -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
    
    if curl -f "https://${api_url}/health" &> /dev/null; then
        success "API health check passed"
    else
        error "API health check failed"
    fi
    
    # Check database connectivity
    if kubectl exec -n kopitar deployment/kopitar-api -- python -c "
import asyncio
from kopitar.database.connection import test_connection
asyncio.run(test_connection())
" &> /dev/null; then
        success "Database connectivity check passed"
    else
        error "Database connectivity check failed"
    fi
    
    success "All health checks passed"
}

backup_configuration() {
    log "Backing up configuration..."
    
    local backup_dir="${SCRIPT_DIR}/backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "${backup_dir}"
    
    # Backup Terraform state
    terraform -chdir="${TERRAFORM_DIR}" show -json > "${backup_dir}/terraform-state.json"
    
    # Backup Kubernetes configs
    kubectl get all -n kopitar -o yaml > "${backup_dir}/kubernetes-resources.yaml"
    
    # Backup environment variables (without secrets)
    env | grep -E '^(ENVIRONMENT|AWS_REGION|CLUSTER_NAME)=' > "${backup_dir}/environment.env"
    
    success "Configuration backed up to ${backup_dir}"
}

cleanup_on_failure() {
    warning "Deployment failed. Cleaning up resources..."
    
    # Destroy Terraform infrastructure if it exists
    if [[ -f "${TERRAFORM_DIR}/terraform.tfstate" ]]; then
        terraform -chdir="${TERRAFORM_DIR}" destroy -auto-approve \
            -var="environment=${ENVIRONMENT}" \
            -var="aws_region=${AWS_REGION}" \
            -var="db_password=dummy" \
            -var="redis_auth_token=dummy" || true
    fi
    
    warning "Cleanup completed"
}

print_summary() {
    echo
    echo "=========================================="
    echo "Kopitar Platform Deployment Summary"
    echo "=========================================="
    echo "Environment: ${ENVIRONMENT}"
    echo "AWS Region: ${AWS_REGION}"
    echo "Cluster Name: ${CLUSTER_NAME}"
    echo
    echo "Access URLs:"
    
    local api_url
    api_url=$(kubectl get ingress kopitar-api -n kopitar -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "Not available")
    echo "  API: https://${api_url}"
    
    local grafana_url
    grafana_url=$(kubectl get service prometheus-grafana -n monitoring -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "Not available")
    echo "  Grafana: http://${grafana_url}"
    
    echo
    echo "Useful Commands:"
    echo "  kubectl get pods -n kopitar"
    echo "  kubectl logs -f deployment/kopitar-api -n kopitar"
    echo "  helm list -A"
    echo
    echo "Next Steps:"
    echo "  1. Configure domain DNS to point to load balancer"
    echo "  2. Set up SSL certificates"
    echo "  3. Configure monitoring alerts"
    echo "  4. Run initial data backfill"
    echo "=========================================="
}

main() {
    log "Starting Kopitar Platform deployment..."
    
    # Trap to cleanup on failure
    trap cleanup_on_failure ERR
    
    # Pre-flight checks
    check_dependencies
    validate_environment
    
    # Deployment steps
    setup_terraform_backend
    deploy_infrastructure
    configure_kubectl
    install_cluster_components
    deploy_application
    run_health_checks
    backup_configuration
    
    # Summary
    print_summary
    
    success "Kopitar Platform deployed successfully!"
}

# Script usage
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Deploy the Kopitar NHL Analytics Platform to AWS

OPTIONS:
    -e, --environment     Environment to deploy (dev, staging, prod) [default: prod]
    -r, --region         AWS region [default: us-east-1]
    -a, --auto-approve   Auto-approve Terraform changes
    -h, --help           Show this help message

ENVIRONMENT VARIABLES:
    DB_PASSWORD          PostgreSQL password (required)
    REDIS_AUTH_TOKEN     Redis authentication token (required)
    JWT_SECRET_KEY       JWT signing key (required)
    SECRET_KEY           Application secret key (required)
    GRAFANA_PASSWORD     Grafana admin password (optional)

EXAMPLES:
    # Deploy to production
    export DB_PASSWORD="secure_password"
    export REDIS_AUTH_TOKEN="redis_token"
    export JWT_SECRET_KEY="jwt_secret"
    export SECRET_KEY="app_secret"
    $0

    # Deploy to staging with auto-approval
    $0 -e staging -a

    # Deploy to specific region
    $0 -r us-west-2

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -r|--region)
            AWS_REGION="$2"
            shift 2
            ;;
        -a|--auto-approve)
            AUTO_APPROVE=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            ;;
    esac
done

# Run main function
main "$@"