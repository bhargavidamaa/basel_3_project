from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, DecimalType
from pyspark.sql.functions import col, sum as _sum, when, round as _round

# 1. Initialize Spark Session
# We name our app clearly so we can track it in the Spark UI
spark = SparkSession.builder \
    .appName("Basel_III_NPL_Computation") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

# Define paths (pointing to the mapped Docker volume)
DATA_DIR = "/opt/airflow/data"

print("--- Starting NPL Computation Pipeline ---")

# 2. Strict Schema Definition
# Senior DE Tip: We use DecimalType(18, 2) to prevent floating-point arithmetic errors.
# FloatType() will create "phantom pennies" when aggregating millions of rows.
asset_schema = StructType([
    StructField("asset_id", StringType(), False),
    StructField("branch_id", StringType(), False),
    StructField("asset_type", StringType(), True),
    StructField("balance", DecimalType(18, 2), True),
    StructField("risk_weight", DecimalType(5, 2), True),
    StructField("hqla_level", StringType(), True),
    StructField("loan_status", StringType(), True)
])

# 3. Ingest Data
print("Ingesting assets.csv...")
df_assets = spark.read.csv(
    f"{DATA_DIR}/assets.csv", 
    header=True, 
    schema=asset_schema
)

# 4. Metric Computation: NPL Ratio
# Rule: NPL Ratio = Non-Performing Loans / Total Loans
print("Computing NPL Ratio at Bank and Branch levels...")

# Filter for only loan assets (ignore cash, bonds, etc.)
df_loans = df_assets.filter(col("loan_status") != 'N/A')

# Calculate at the Branch Level
df_branch_npl = df_loans.groupBy("branch_id").agg(
    _sum("balance").alias("total_loan_balance"),
    _sum(when(col("loan_status") == 'Non-Performing', col("balance")).otherwise(0)).alias("npl_balance")
).withColumn(
    "npl_ratio_percent", 
    _round((col("npl_balance") / col("total_loan_balance")) * 100, 2)
)

# Calculate at the Aggregate Bank Level
df_bank_npl = df_loans.agg(
    _sum("balance").alias("total_loan_balance"),
    _sum(when(col("loan_status") == 'Non-Performing', col("balance")).otherwise(0)).alias("npl_balance")
).withColumn(
    "npl_ratio_percent", 
    _round((col("npl_balance") / col("total_loan_balance")) * 100, 2)
).withColumn("entity", col("total_loan_balance") * 0 + 1) # Dummy column for display

# 5. Output Results
print("\n--- Branch Level NPL Ratios (Top 5) ---")
df_branch_npl.orderBy(col("npl_ratio_percent").desc()).show(5)

print("--- Aggregate Bank Level NPL Ratio ---")
df_bank_npl.select("total_loan_balance", "npl_balance", "npl_ratio_percent").show()

spark.stop()