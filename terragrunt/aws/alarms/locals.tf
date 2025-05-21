locals {
  data_lake_namespace                      = "data-lake"
  glue_crawler_metric_filter_error_pattern = "ERROR"
  glue_crawler_error_metric_name           = "glue-crawler-error"

  glue_etl_pythonshell_error_metric_name           = "glue-etl-pythonshell-error"
  glue_etl_pythonshell_metric_filter_error_pattern = "ERROR"
  glue_etl_spark_error_metric_name                 = "glue-etl-spark-error"
  glue_etl_spark_metric_filter_error_pattern       = "[(w1=\"*ERROR*com.amazonaws.services.glue.log.GlueLogger*\")]"
}