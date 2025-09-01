#!/bin/bash

# Tawnia Healthcare Analytics - Deployment Script
# Supports multiple deployment targets: Docker, Cloudflare, Netlify

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
DEPLOYMENT_TARGET="docker"
ENVIRONMENT="production"
SKIP_TESTS=false
SKIP_BUILD=false
VERBOSE=false

# Help function
show_help() {
    cat << EOF
Tawnia Healthcare Analytics Deployment Script

Usage: $0 [OPTIONS]

Options:
    -t, --target TARGET       Deployment target (docker, cloudflare, netlify, all)
    -e, --environment ENV     Environment (development, staging, production)
    -s, --skip-tests         Skip running tests
    -b, --skip-build         Skip building the application
    -v, --verbose            Enable verbose output
    -h, --help               Show this help message

Examples:
    $0 --target docker --environment production
    $0 --target cloudflare --skip-tests
    $0 --target all --environment staging

Supported targets:
    docker      - Build and run Docker container locally
    cloudflare  - Deploy to Cloudflare Workers and Pages
    netlify     - Deploy to Netlify
    all         - Deploy to all supported platforms
EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--target)
            DEPLOYMENT_TARGET="$2"
            shift 2
            ;;
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -s|--skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        -b|--skip-build)
            SKIP_BUILD=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_verbose() {
    if [ "$VERBOSE" = true ]; then
        echo -e "${BLUE}[VERBOSE]${NC} $1"
    fi
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check if we're in the right directory
    if [ ! -f "main_enhanced.py" ]; then
        log_error "main_enhanced.py not found. Please run this script from the project root."
        exit 1
    fi

    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is required but not installed."
        exit 1
    fi

    # Check pip
    if ! command -v pip3 &> /dev/null; then
        log_error "pip3 is required but not installed."
        exit 1
    fi

    # Check Node.js for Cloudflare deployment
    if [[ "$DEPLOYMENT_TARGET" == "cloudflare" || "$DEPLOYMENT_TARGET" == "all" ]]; then
        if ! command -v node &> /dev/null; then
            log_warning "Node.js not found. Cloudflare deployment will be skipped."
        fi
    fi

    # Check Docker for Docker deployment
    if [[ "$DEPLOYMENT_TARGET" == "docker" || "$DEPLOYMENT_TARGET" == "all" ]]; then
        if ! command -v docker &> /dev/null; then
            log_warning "Docker not found. Docker deployment will be skipped."
        fi
    fi

    log_success "Prerequisites check completed"
}

# Setup environment
setup_environment() {
    log_info "Setting up environment for $ENVIRONMENT..."

    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            log_info "Created .env file from .env.example"
        else
            log_warning ".env file not found and no .env.example to copy from"
        fi
    fi

    # Set environment-specific variables
    case $ENVIRONMENT in
        "development")
            export DEBUG=true
            export LOG_LEVEL=DEBUG
            ;;
        "staging")
            export DEBUG=false
            export LOG_LEVEL=INFO
            ;;
        "production")
            export DEBUG=false
            export LOG_LEVEL=WARNING
            ;;
    esac

    log_success "Environment setup completed"
}

# Install dependencies
install_dependencies() {
    log_info "Installing Python dependencies..."

    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        log_info "Created virtual environment"
    fi

    # Activate virtual environment
    source venv/bin/activate

    # Upgrade pip
    pip install --upgrade pip

    # Install requirements
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        log_success "Python dependencies installed"
    else
        log_error "requirements.txt not found"
        exit 1
    fi
}

# Run tests
run_tests() {
    if [ "$SKIP_TESTS" = true ]; then
        log_info "Skipping tests as requested"
        return 0
    fi

    log_info "Running tests..."

    # Activate virtual environment
    source venv/bin/activate

    # Run pytest if available
    if command -v pytest &> /dev/null; then
        pytest tests/ -v --tb=short
        if [ $? -eq 0 ]; then
            log_success "All tests passed"
        else
            log_error "Some tests failed"
            exit 1
        fi
    else
        # Run the enhanced test script
        if [ -f "test_enhanced_system.py" ]; then
            python test_enhanced_system.py
            if [ $? -eq 0 ]; then
                log_success "Enhanced system tests passed"
            else
                log_error "Enhanced system tests failed"
                exit 1
            fi
        else
            log_warning "No test files found"
        fi
    fi
}

# Build application
build_application() {
    if [ "$SKIP_BUILD" = true ]; then
        log_info "Skipping build as requested"
        return 0
    fi

    log_info "Building application..."

    # Create dist directory
    mkdir -p dist

    # Copy main files
    cp main_enhanced.py dist/
    cp -r src/ dist/
    cp requirements.txt dist/

    # Copy configuration files
    if [ -f ".env" ]; then
        cp .env dist/
    fi

    # Create version file
    echo "BUILD_DATE=$(date -u +%Y-%m-%dT%H:%M:%SZ)" > dist/version.txt
    echo "ENVIRONMENT=$ENVIRONMENT" >> dist/version.txt
    echo "GIT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')" >> dist/version.txt

    log_success "Application built successfully"
}

# Deploy to Docker
deploy_docker() {
    log_info "Deploying to Docker..."

    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        return 1
    fi

    # Build Docker image
    docker build -t tawnia-analytics:latest .

    if [ $? -eq 0 ]; then
        log_success "Docker image built successfully"

        # Stop existing container if running
        docker stop tawnia-analytics 2>/dev/null || true
        docker rm tawnia-analytics 2>/dev/null || true

        # Run new container
        docker run -d \
            --name tawnia-analytics \
            -p 8000:8000 \
            --env-file .env \
            tawnia-analytics:latest

        if [ $? -eq 0 ]; then
            log_success "Docker container deployed successfully"
            log_info "Application is running at http://localhost:8000"
        else
            log_error "Failed to start Docker container"
            return 1
        fi
    else
        log_error "Failed to build Docker image"
        return 1
    fi
}

# Deploy to Cloudflare
deploy_cloudflare() {
    log_info "Deploying to Cloudflare..."

    if ! command -v node &> /dev/null; then
        log_error "Node.js is not installed"
        return 1
    fi

    # Check if wrangler is installed
    if ! command -v wrangler &> /dev/null; then
        log_info "Installing Wrangler CLI..."
        npm install -g wrangler
    fi

    # Deploy worker
    if [ -f "wrangler.toml" ]; then
        wrangler deploy

        if [ $? -eq 0 ]; then
            log_success "Cloudflare Worker deployed successfully"
        else
            log_error "Failed to deploy Cloudflare Worker"
            return 1
        fi
    else
        log_error "wrangler.toml not found"
        return 1
    fi

    # Deploy Pages (if configured)
    if [ -d "frontend" ]; then
        log_info "Deploying frontend to Cloudflare Pages..."
        wrangler pages deploy frontend --project-name tawnia-analytics

        if [ $? -eq 0 ]; then
            log_success "Cloudflare Pages deployed successfully"
        else
            log_warning "Failed to deploy Cloudflare Pages"
        fi
    fi
}

# Deploy to Netlify
deploy_netlify() {
    log_info "Deploying to Netlify..."

    # Check if netlify CLI is installed
    if ! command -v netlify &> /dev/null; then
        log_info "Installing Netlify CLI..."
        npm install -g netlify-cli
    fi

    # Deploy to Netlify
    if [ -f "netlify.toml" ]; then
        netlify deploy --prod

        if [ $? -eq 0 ]; then
            log_success "Netlify deployment completed successfully"
        else
            log_error "Failed to deploy to Netlify"
            return 1
        fi
    else
        log_error "netlify.toml not found"
        return 1
    fi
}

# Main deployment function
deploy() {
    case $DEPLOYMENT_TARGET in
        "docker")
            deploy_docker
            ;;
        "cloudflare")
            deploy_cloudflare
            ;;
        "netlify")
            deploy_netlify
            ;;
        "all")
            deploy_docker
            deploy_cloudflare
            deploy_netlify
            ;;
        *)
            log_error "Unknown deployment target: $DEPLOYMENT_TARGET"
            log_info "Supported targets: docker, cloudflare, netlify, all"
            exit 1
            ;;
    esac
}

# Cleanup function
cleanup() {
    log_info "Cleaning up..."

    # Deactivate virtual environment if active
    if [[ "$VIRTUAL_ENV" != "" ]]; then
        deactivate
    fi

    log_success "Cleanup completed"
}

# Main execution
main() {
    log_info "Starting deployment process..."
    log_info "Target: $DEPLOYMENT_TARGET"
    log_info "Environment: $ENVIRONMENT"

    # Set trap for cleanup on exit
    trap cleanup EXIT

    check_prerequisites
    setup_environment
    install_dependencies
    run_tests
    build_application
    deploy

    log_success "Deployment process completed successfully!"

    # Show deployment URLs
    case $DEPLOYMENT_TARGET in
        "docker")
            log_info "Application URL: http://localhost:8000"
            ;;
        "cloudflare")
            log_info "Check Cloudflare dashboard for deployment URLs"
            ;;
        "netlify")
            log_info "Check Netlify dashboard for deployment URLs"
            ;;
        "all")
            log_info "Application URLs:"
            log_info "  Docker: http://localhost:8000"
            log_info "  Cloudflare: Check dashboard"
            log_info "  Netlify: Check dashboard"
            ;;
    esac
}

# Run main function
main "$@"
