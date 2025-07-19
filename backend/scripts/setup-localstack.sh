#!/bin/bash

# LocalStack S3 Setup Script for Image Poet

echo "🚀 Setting up LocalStack S3 for Image Poet..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Start LocalStack
echo "📦 Starting LocalStack..."
docker-compose -f docker-compose.localstack.yml up -d

# Wait for LocalStack to be ready
echo "⏳ Waiting for LocalStack to be ready..."
sleep 10

# Check LocalStack health
echo "🔍 Checking LocalStack health..."
for i in {1..30}; do
    if curl -s http://localhost:4566/health > /dev/null; then
        echo "✅ LocalStack is healthy!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ LocalStack failed to start properly"
        exit 1
    fi
    echo "⏳ Waiting... ($i/30)"
    sleep 2
done

# Create S3 bucket
echo "🪣 Creating S3 bucket: image-poet-local"
aws --endpoint-url=http://localhost:4566 s3 mb s3://image-poet-local 2>/dev/null || {
    echo "📝 Bucket might already exist, continuing..."
}

# Verify bucket creation
echo "📋 Listing S3 buckets:"
aws --endpoint-url=http://localhost:4566 s3 ls

# Set up bucket for public read access (for testing)
echo "🔧 Configuring bucket policy..."
cat > /tmp/bucket-policy.json << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::image-poet-local/*"
        }
    ]
}
EOF

aws --endpoint-url=http://localhost:4566 s3api put-bucket-policy \
    --bucket image-poet-local \
    --policy file:///tmp/bucket-policy.json

# Test bucket access
echo "🧪 Testing bucket access..."
echo "Hello LocalStack!" > /tmp/test-file.txt
aws --endpoint-url=http://localhost:4566 s3 cp /tmp/test-file.txt s3://image-poet-local/test.txt

# Verify file upload
if aws --endpoint-url=http://localhost:4566 s3 ls s3://image-poet-local/test.txt > /dev/null; then
    echo "✅ File upload test successful!"
    # Clean up test file
    aws --endpoint-url=http://localhost:4566 s3 rm s3://image-poet-local/test.txt
    rm /tmp/test-file.txt /tmp/bucket-policy.json
else
    echo "❌ File upload test failed"
    exit 1
fi

echo ""
echo "🎉 LocalStack S3 setup complete!"
echo ""
echo "📝 Next steps:"
echo "1. Copy LocalStack environment: cp .env.localstack .env"
echo "2. Start your FastAPI server: uvicorn app.main:app --reload"
echo "3. Test image upload at: http://localhost:8000/docs"
echo ""
echo "🔧 Useful commands:"
echo "  - Check S3 buckets: aws --endpoint-url=http://localhost:4566 s3 ls"
echo "  - List bucket contents: aws --endpoint-url=http://localhost:4566 s3 ls s3://image-poet-local/"
echo "  - Stop LocalStack: docker-compose -f docker-compose.localstack.yml down"
echo ""