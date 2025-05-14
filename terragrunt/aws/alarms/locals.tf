locals {
  anomaly_detection_alarms = [
    {
      name               = "platform-gc-forms-etl-submissions-processed-record"
      namespace          = "data-lake/etl/gc-forms"
      dataset            = "processed-data/submissions"
      metric_name        = "ProcessedRecordCount"
      standard_deviation = 2
    },
    {
      name               = "platform-gc-forms-etl-template-processed-record"
      namespace          = "data-lake/etl/gc-forms"
      dataset            = "processed-data/template"
      metric_name        = "ProcessedRecordCount"
      standard_deviation = 2
    },
    {
      name               = "platform-gc-forms-etl-template-to-user-processed-record"
      namespace          = "data-lake/etl/gc-forms"
      dataset            = "processed-data/templateToUser"
      metric_name        = "ProcessedRecordCount"
      standard_deviation = 2
    },
    {
      name               = "platform-gc-forms-etl-user-processed-record"
      namespace          = "data-lake/etl/gc-forms"
      dataset            = "processed-data/user"
      metric_name        = "ProcessedRecordCount"
      standard_deviation = 2
    },
    {
      name               = "platform-gc-notify-etl-notification-history-processed-record"
      namespace          = "data-lake/etl/gc-notify"
      dataset            = "notification_history"
      metric_name        = "ProcessedRecordCount"
      standard_deviation = 2
    },
    {
      name               = "platform-gc-notify-etl-notifications-processed-record"
      namespace          = "data-lake/etl/gc-notify"
      dataset            = "notifications"
      metric_name        = "ProcessedRecordCount"
      standard_deviation = 2
    },
    {
      name               = "platform-gc-notify-etl-users-processed-record"
      namespace          = "data-lake/etl/gc-notify"
      dataset            = "users"
      metric_name        = "ProcessedRecordCount"
      standard_deviation = 2
    }
  ]

  data_lake_namespace                      = "data-lake"
  glue_crawler_metric_filter_error_pattern = "ERROR"
  glue_crawler_error_metric_name           = "glue-crawler-error"
  glue_etl_metric_filter_error_pattern     = "ERROR"
  glue_etl_error_metric_name               = "glue-etl-error"
}