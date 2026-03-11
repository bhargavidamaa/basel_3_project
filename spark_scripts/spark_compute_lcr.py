from pyspark.sql import SparkSession, Window
from pyspark.sql.types import StructType, StructField, StringType, DecimalType
from pyspark.sql.functions import col, sum as _sum, when, rand, expr

spark = SparkSession.builder.appName("Basel_III_LCR_Computation").getOrCreate()
spark.sparkContext.setLogLevel("WARN")

DATA_DIR = "/opt/airflow/data"

print("--- Starting LCR Computation ---")

# 1. Ingest Data (Assuming schemas are defined similarly to previous scripts)
df_assets = spark.read.csv(f"{DATA_DIR}/assets.csv", header=True, inferSchema=True)
df_liabilities = spark.read.csv(f"{DATA_DIR}/liabilities.csv", header=True, inferSchema=True)

# 2. Calculate HQLA (High Quality Liquid Assets)
# Level 1 gets 100% value, Level 2A gets 85% value (15% regulatory haircut)
df_hqla = df_assets.withColumn(
    "hqla_value",
    when(col("hqla_level") == "Level 1", col("balance"))
    .when(col("hqla_level") == "Level 2A", col("balance") * 0.85)
    .otherwise(0)
)
total_hqla = df_hqla.agg(_sum("hqla_value").alias("total_hqla")).collect()[0]["total_hqla"]

# 3. Calculate 30-Day Rolling Outflows using Window Functions
# First, simulate a 'maturity_days' column (0 to 60 days) to represent when funds might leave
df_liab_timed = df_liabilities.withColumn("maturity_days", (rand() * 60).cast("integer")) \
                              .withColumn("projected_outflow", col("balance") * col("outflow_rate"))

# Define a Window spanning the next 30 days
# This calculates the cumulative rolling risk of capital flight over a 30-day period
window_30_days = Window.partitionBy("branch_id").orderBy("maturity_days").rangeBetween(0, 30)

df_rolling_outflows = df_liab_timed.withColumn(
    "rolling_30d_outflow", 
    _sum("projected_outflow").over(window_30_days)
)

# For the bank-wide LCR, we just sum all outflows occurring within <= 30 days
total_30d_outflow = df_liab_timed.filter(col("maturity_days") <= 30) \
                                 .agg(_sum("projected_outflow").alias("net_outflow")) \
                                 .collect()[0]["net_outflow"]

# 4. Calculate LCR
lcr_ratio = (total_hqla / total_30d_outflow) * 100
print(f"Total HQLA: ${total_hqla:,.2f}")
print(f"Net 30-Day Cash Outflows: ${total_30d_outflow:,.2f}")
print(f"Liquidity Coverage Ratio (LCR): {lcr_ratio:.2f}% (Regulatory Minimum is usually 100%)")

spark.stop()