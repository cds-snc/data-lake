locals {
  data_lake_namespace                      = "data-lake"
  glue_crawler_metric_filter_error_pattern = "ERROR"
  glue_crawler_error_metric_name           = "glue-crawler-error"

  glue_etl_pythonshell_error_metric_name           = "glue-etl-pythonshell-error"
  glue_etl_pythonshell_metric_filters              = ["ERROR"]
  glue_etl_pythonshell_metric_filters_skip         = ["No new historical-data data found.", "pip's dependency resolver"]
  glue_etl_pythonshell_metric_filter_error_pattern = "[(w1=\"*${join("*\" || w1=\"*", local.glue_etl_pythonshell_metric_filters)}*\") && w1!=\"*${join("*\" && w1!=\"*", local.glue_etl_pythonshell_metric_filters_skip)}*\"]"

  glue_etl_spark_error_metric_name           = "glue-etl-spark-error"
  glue_etl_spark_metric_filter_error_pattern = "[(w1=\"*ERROR*com.amazonaws.services.glue.log.GlueLogger*\")]"

  glue_etl_metric_filter_anomaly_pattern   = "Anomaly"
  glue_etl_pythonshell_anomaly_metric_name = "glue-etl-pythonshell-anomaly"
  glue_etl_spark_anomaly_metric_name       = "glue-etl-spark-anomaly"
}