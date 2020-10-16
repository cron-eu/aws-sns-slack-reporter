# S3 Bucket to store the lambda zip files and the cloudformation template
S3_BUCKET := cron-aws-sns-slack-reporter
VERSION := $(shell git describe --tags)

# S3 Bucket will be created for that region
AWS_REGION := eu-central-1

dist_dir = ./dist
lambda_zip = $(dist_dir)/lambda-${VERSION}.zip

srcs = $(wildcard src/*.py)

.PHONY: build clean create-s3-bucket push-lambda push-cloudformation

all: clean build push-lambda push-cloudformation

build: $(dist_dir) $(lambda_zip)

create-s3-bucket:
	aws s3api create-bucket --bucket ${S3_BUCKET} --region ${AWS_REGION} --create-bucket-configuration LocationConstraint=${AWS_REGION}

$(lambda_zip): $(srcs)
	zip -j -X $@ $^

clean:
	rm -rf $(dist_dir)

$(dist_dir):
	mkdir -p $@

# we sync only the zip file and make it public readable
push-lambda: $(lambda_zip)
	aws s3 sync $(dir $<) s3://${S3_BUCKET}/
	aws s3api put-object-acl --bucket ${S3_BUCKET} --key $(notdir $<) --acl public-read

push-cloudformation: $(wildcard cloudformation/*.yml)
	aws s3 cp $^ s3://${S3_BUCKET}/
	aws s3api put-object-acl --bucket ${S3_BUCKET} --key $(notdir $<) --acl public-read
