"""
AWS Lambda function to process a CSV file from S3, filter specific metrics,
and save the processed file back to S3.
"""

from io import StringIO
import json
import boto3
import pandas as pd
import csv
from botocore.exceptions import ClientError

FILTERS = {
    'environmental': [
        "CO2DIRECTSCOPE1", "CO2INDIRECTSCOPE2", "CO2INDIRECTSCOPE3",
        "CO2_NO_EQUIVALENTS", "NOXEMISSIONS", "SOXEMISSIONS",
        "VOCEMISSIONS",
        "WASTETOTAL", "HAZARDOUSWASTE", "PARTICULATE_MATTER_EMISSIONS",
        "AIRPOLLUTANTS_DIRECT", "AIRPOLLUTANTS_INDIRECT",
        "NATURAL_RESOURCE_USE_DIRECT", "WATERWITHDRAWALTOTAL",
        "WATER_USE_PAI_M10", "TOXIC_CHEMICALS_REDUCTION",
        "VOC_EMISSIONS_REDUCTION", "N_OXS_OX_EMISSIONS_REDUCTION", 
        "ECO_DESIGN_PRODUCTS", "ENERGYUSETOTAL", "ENV_INVESTMENTS", 
        "POLICY_EMISSIONS", "POLICY_SUSTAINABLE_PACKAGING", 
        "POLICY_WATER_EFFICIENCY", "RENEWENERGYCONSUMED", 
        "RENEWENERGYPRODUCED", "RENEWENERGYPURCHASED", 
        "SUSTAINABLE_BUILDING_PRODUCTS", "TAKEBACK_RECYCLING_INITIATIVES",
        "TARGETS_EMISSIONS", "TARGETS_WATER_EFFICIENCY",
        "TRANALYTICRENEWENERGYUSE", "WASTE_RECYCLED", 
        "WASTE_REDUCTION_TOTAL", "WATER_TECHNOLOGIES"
    ],
    'social': [
        "BRIBERY_AND_CORRUPTION_PAI_INSUFFICIENT_ACTIONS",                     
        "EMPLOYEEFATALITIES", "EMPLOYEE_HEALTH_SAFETY_POLICY", 
        "GENDER_PAY_GAP_PERCENTAGE",
        "HUMAN_RIGHTS_VIOLATION_PAI"
        "IMPROVEMENT_TOOLS_BUSINESS_ETHICS", "LOSTWORKINGDAYS", 
        "POLICY_BOARD_DIVERSITY", "POLICY_BRIBERYAND_CORRUPTION",
        "POLICY_BUSINESS_ETHICS", "POLICY_CHILD_LABOR", "POLICY_DATA_PRIVACY", 
        "POLICY_FORCED_LABOR", "POLICY_HUMAN_RIGHTS", "SUPPLY_CHAINHS_POLICY",
        "TIRTOTAL", "TURNOVEREMPLOYEES", "ANALYTICCSR_COMP_INCENTIVES", 
        "ANALYTICEMPLOYMENTCREATION", "ANALYTICTOTALDONATIONS", 
        "ANIMAL_TESTING_REDUCTION", "AVGTRAININGHOURS", 
        "CONFORMANCE_OECD_MNE", "CONFORMANCE_UN_GUID", "DAY_CARE_SERVICES",
        "GRIEVANCE_REPORTING_PROCESS", "HUMAN_RIGHTS_CONTRACTOR", 
        "HUMAN_RIGHTS_POLICY_DUEDILIGENCE", "ISO14000", "LABELED_WOOD",
        "POLICY_FREEDOMOF_ASSOCIATION", "TARGETS_DIVERSITY_OPPORTUNITY", 
        "TRADEUNIONREP", "WHISTLEBLOWER_PROTECTION", "WOMENEMPLOYEES", 
        "WOMENMANAGERS"
    ],
    'governance': [
        "ANALYTIC_ANTI_TAKEOVER_DEVICES", "ANALYTICNONAUDITAUDITFEESRATIO",
        "ANNUAL_MEDIAN_COMPENSATION", "AUDITCOMMNONEXECMEMBERS",
        "CALL_MEETINGS_LIMITED_RIGHTS", "CEO_ANNUAL_COMPENSATION",
        "CEO_PAY_RATIO_MEDIAN", "COMPCOMMNONEXECMEMBERS",
        "CSR_REPORTING_EXTERNAL_AUDIT", "CSR_REPORTINGGRI",
        "CSR_REPORTINGISO26000", "ANALYTICAUDITCOMMIND", 
        "ANALYTICBOARDFEMALE", "ANALYTICCEO_CHAIRMAN_SEPARATION",
        "ANALYTICCOMPCOMMIND", "ANALYTICINDEPBOARD", 
        "ANALYTICNOMINATIONCOMMIND", "ANALYTICNONEXECBOARD", "ANALYTICQMS",
        "ANALYTICWASTERECYCLINGRATIO", "ANALYTIC_AUDIT_COMM_EXPERTISE", 
        "ANALYTIC_VOTING_RIGHTS", "BOARDMEETINGATTENDANCEAVG", 
        "COMMMEETINGSATTENDANCEAVG", "GLOBAL_COMPACT"
    ]
}

def lambda_handler(event, _context):
    """
    AWS Lambda handler function that processes a CSV file from S3, filters
    specific metrics, and stores the processed CSV back in S3.

    Parameters:
        event (dict): The AWS Lambda event object, triggered by an S3 upload.
        context (object): The AWS Lambda runtime context.

    Returns:
        dict: A response dictionary containing the statusCode and body message.
    """

    # Constants
    upload_prefix = "processedCSV/"

    # AWS S3 Client
    s3_client = boto3.client("s3")
    # New data uploaded and exisitng file to be amended
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    new_key = event["Records"][0]["s3"]["object"]["key"]

    lower_key = new_key.lower()
    if "environment" in lower_key:
        data_pillar = "environmental"
    elif "social" in lower_key:
        data_pillar = "social"
    elif "governance" in lower_key:
        data_pillar = "governance"
    else:
        data_pillar = "unknown"

    existing_key = f"{upload_prefix}{data_pillar}.csv"

    try:
        print("🚀 Starting CSV processing...")
        print("📩 Event received:", json.dumps(event))

        # Get the data from the newly uploaded raw CSV file
        new_csv = s3_client.get_object(Bucket=bucket, Key=new_key)
        raw_bytes = new_csv["Body"].read()
        raw_str = raw_bytes.decode("utf-8")

        # Get the delimiter
        try:
            sample = raw_str[:1024]
            dialect = csv.Sniffer().sniff(sample)
            delimiter = dialect.delimiter
        except csv.Error:
            delimiter = ","

        new_data = pd.read_csv(StringIO(raw_str), sep=delimiter)

        print(f"🔍 Fetching existing files in {upload_prefix}")
        try:
            exist_csv = s3_client.get_object(Bucket=bucket, Key=existing_key)
            exist_data = pd.read_csv(exist_csv["Body"])
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                print("✅ No existing processed file found.")
                exist_data = pd.DataFrame()
            else:
                raise

        # Combine and deduplicate data
        combined = pd.concat([exist_data, new_data], ignore_index=True)
        combined.drop_duplicates(inplace=True)

        # Log column names to check if "metric_name" exists
        print("🧐 Combined CSV Columns:", combined.columns.tolist())

        # Define filter list
        metric_filter = FILTERS.get(data_pillar, [])
        if not metric_filter:
            print(f"❌ No filters found for risk type: {data_pillar}")
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "error": f"No filters found for risk type: {data_pillar}"})
            }

        # Log unique metric names before filtering
        if "metric_name" not in combined.columns:
            print("❌ 'metric_name' column not found! Check CSV format.")
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "error": "Missing 'metric_name' column in CSV"})
            }

        # Filter data based on metric_name
        unique_metrics = combined["metric_name"].unique().tolist()
        print(f"🔍 Unique metric_name values: {unique_metrics}")

        processed_df = combined[combined["metric_name"].isin(metric_filter)]
        print(f"✅ Filtered DataFrame rows: {len(processed_df)}")

        # Save final processed CSV to S3
        out_buffer = StringIO()
        processed_df.to_csv(out_buffer, index=False)
        s3_client.put_object(
            Bucket=bucket,
            Key=existing_key,
            Body=out_buffer.getvalue(),
            ContentType="text/csv",
        )
        print("🎉 CSV processing completed and amenended successfully.")

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "status": "CSV processed and amended successfully"
            }),
        }

    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"❌ Error: {str(e)}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}


def concat_all_data(bucket, upload_prefix):  
    """
    Concatenate all data from the processed CSV files in S3 into a single
    DataFrame and uploads it as a master CSV file.

    Parameters:
        bucket (str): The name of the S3 bucket.
        upload_prefix (str): The prefix for the uploaded files.
    """
    s3_client = boto3.client("s3")

    paginator = s3_client.get_paginator("list_objects_v2")
    pages = paginator.paginate(Bucket=bucket, Prefix=upload_prefix)

    print("🔍 Concatonating all CSV files ...")

    all_data = []
    for page in pages:
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.endswith(".csv") and not key.endswith("master.csv"):
                response = s3_client.get_object(Bucket=bucket, Key=key)
                data = pd.read_csv(response["Body"])
                all_data.append(data)

    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)

        out_buffer = StringIO()
        combined_df.to_csv(out_buffer, index=False)

        # Write all data to master csv file
        s3_client.put_object(
            Bucket=bucket,
            Key=f"{upload_prefix}master.csv",
            Body=out_buffer.getvalue()
        )
        print("🎉 All data concatenated and saved to master.csv")