import boto3
import json
from datetime import datetime


def blog_generate_using_bedrock(blogtopic: str) -> str:
    try:
        bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")

        response = bedrock.converse(
            modelId="meta.llama3-8b-instruct-v1:0",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "text": f"Write a detailed 2000-word blog post on the topic: {blogtopic}"
                        }
                    ],
                }
            ],
            inferenceConfig={
                "temperature": 0.5,
                "maxTokens": 1000
            }
        )

        blog_details = response["output"]["message"]["content"][0]["text"]
        return blog_details

    except Exception as e:
        print(f"Bedrock Error: {e}")
        return ""


def save_blog_details_s3(s3_key, s3_bucket, generate_blog):
    s3 = boto3.client("s3")
    try:
        s3.put_object(
            Bucket=s3_bucket,
            Key=s3_key,
            Body=generate_blog,
            ContentType="text/plain"
        )
        print(f"Saved to S3: {s3_bucket}/{s3_key}")
        return True

    except Exception as e:
        print(f"S3 Error: {e}")
        return False


def lambda_handler(event, context):
    try:
        # Handle API Gateway event
        if "body" in event:
            body = json.loads(event["body"])
        else:
            body = event

        blogtopic = body.get("blog_topic")

        if not blogtopic:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "blog_topic is required"})
            }

        generate_blog = blog_generate_using_bedrock(blogtopic)

        if generate_blog:
            current_time = datetime.now().strftime("%Y%m%d-%H%M%S")
            s3_key = f"blog-output/{current_time}.txt"
            s3_bucket = "mj-blog-posts-bucket"

            save_blog_details_s3(s3_key, s3_bucket, generate_blog)

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Blog generated successfully",
                "blog_details": generate_blog
            })
        }

    except Exception as e:
        print(f"Lambda Error: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }