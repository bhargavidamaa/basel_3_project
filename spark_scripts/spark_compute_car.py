from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, DecimalType
from pyspark.sql.functions import col, sum as _sum, broadcast, round as _round
from decimal import Decimal

spark = SparkSession.builder.appName("Basel_III_CAR_Computation").getOrCreate()
spark.sparkContext.setLogLevel("WARN")

DATA_DIR = "/opt/airflow/data"

print("--- Starting CAR Computation ---")

# 1. Define Schemas
asset_schema = StructType([
    StructField("asset_id", StringType(), False),
    StructField("branch_id", StringType(), False),
    StructField("asset_type", StringType(), True),
    StructField("balance", DecimalType(18, 2), True),
    StructField("risk_weight", DecimalType(5, 2), True) # We could read this from assets, but let's join it to demonstrate the skill
])

capital_schema = StructType([
    StructField("capital_id", StringType(), False),
    StructField("capital_type", StringType(), True),
    StructField("balance", DecimalType(18, 2), True)
])

# 2. Ingest Data
df_assets = spark.read.csv(f"{DATA_DIR}/assets.csv", header=True, schema=asset_schema)
df_capital = spark.read.csv(f"{DATA_DIR}/capital.csv", header=True, schema=capital_schema)

# 3. Create Reference Data (Config Table) for Broadcast
config_data = [
    ("Cash", 0.00), ("Government Bonds", 0.00), ("Corporate Bonds", 0.50),
    ("Residential Mortgage", 0.35), ("Commercial Real Estate", 1.00),
    ("Corporate Loan", 1.00), ("Consumer Loan", 0.75)
]
df_risk_config = spark.createDataFrame(config_data, ["ref_asset_type", "ref_risk_weight"])

# 4. Broadcast Join to calculate RWA
# We broadcast the small config table to the large assets table
df_rwa = df_assets.join(
    broadcast(df_risk_config),
    df_assets.asset_type == df_risk_config.ref_asset_type,
    "left"
).withColumn("risk_weighted_balance", col("balance") * col("ref_risk_weight"))

total_rwa = df_rwa.agg(_sum("risk_weighted_balance").alias("total_rwa")).collect()[0]["total_rwa"]
tier1_capital = df_capital.filter(col("capital_type") == "Tier 1 Capital").agg(_sum("balance").alias("total_capital")).collect()[0]["total_capital"]

# 5. Calculate CAR
car_ratio = (tier1_capital / Decimal(total_rwa)) * 100
print(f"Total Risk-Weighted Assets (RWA): ${total_rwa:,.2f}")
print(f"Total Tier 1 Capital: ${tier1_capital:,.2f}")
print(f"Capital Adequacy Ratio (CAR): {car_ratio:.2f}%")

spark.stop()