resource "aws_athena_named_query" "notify_enriched_delete" {
  name     = "notify_enriched_delete_query"
  database = "platform_gc_notify_${var.env}"
  query = "DROP TABLE IF EXISTS platform_gc_notify_${var.env}.platform_gc_notify_notifications_enriched"
  description = "Drop enriched_notifications query"
  workgroup   = var.athena_curated_workgroup_name
}

resource "aws_athena_named_query" "notify_enriched" {
  name     = "notify_enriched_query"
  database = "platform_gc_notify_${var.env}"
  query = templatefile("${path.module}/queries/notify_enriched.sql.tmpl", {
    curated_bucket = var.curated_bucket_name
    database       = "platform_gc_notify_${var.env}"
    table_name     = "platform_gc_notify_notifications_enriched"
  })
  description = "Create enriched_notifications query"
  workgroup   = var.athena_curated_workgroup_name
}

resource "aws_sfn_state_machine" "etl_state_machine" {
  name     = "GlueOrchestrator"
  role_arn = aws_iam_role.sfn_role.arn
  definition = jsonencode(
    {
      "Comment" : "Orchestrates Glue jobs in parallel and runs Athena notify_enriched as soon as GC Notify job completes",
      "StartAt" : "ParallelGlueJobs",
      "States" : {
        "ParallelGlueJobs" : {
          "Type" : "Parallel",
          "Next" : "AllJobsComplete",
          "Branches" : [
            {
              "StartAt" : "StartGCFormsJob",
              "States" : {
                "StartGCFormsJob" : {
                  "Type" : "Task",
                  "Resource" : "arn:aws:states:::glue:startJobRun.sync",
                  "Parameters" : {
                    "JobName" : var.platform_gc_forms_job_name
                  },
                  "End" : true,
                  "Catch" : [
                    {
                      "ErrorEquals" : ["States.ALL"],
                      "Next" : "GCFormsJobFailed"
                    }
                  ]
                },
                "GCFormsJobFailed" : {
                  "Type" : "Pass",
                  "Result" : "GC Forms Glue job failed",
                  "End" : true
                }
              }
            },
            {
              "StartAt" : "StartGCNotifyJob",
              "States" : {
                "StartGCNotifyJob" : {
                  "Type" : "Task",
                  "Resource" : "arn:aws:states:::glue:startJobRun.sync",
                  "Parameters" : {
                    "JobName" : var.platform_gc_notify_job_name
                  },
                  "Next" : "DropTableIfExists",
                  "Catch" : [
                    {
                      "ErrorEquals" : ["States.ALL"],
                      "Next" : "GCNotifyJobFailed"
                    }
                  ]
                },
                "DropTableIfExists": {
                  "Type": "Task",
                  "Resource": "arn:aws:states:::athena:startQueryExecution.sync",
                  "Parameters": {
                    "QueryString": aws_athena_named_query.notify_enriched_delete.query,
                    "QueryExecutionContext": {
                      "Database": aws_athena_named_query.notify_enriched_delete.database
                    },
                    "WorkGroup": aws_athena_named_query.notify_enriched_delete.workgroup
                  },
                  "Next": "RunNotifyEnrichedAthena",
                  "Catch": [
                    {
                      "ErrorEquals": ["States.ALL"],
                      "Next": "DropTableFailed"
                    }
                  ]
                },
                "DropTableFailed": {
                  "Type": "Pass",
                  "Result": "Drop table failed, skipping create table step",
                  "End": true
                },
                "RunNotifyEnrichedAthena": {
                  "Type": "Task",
                  "Resource": "arn:aws:states:::athena:startQueryExecution.sync",
                  "Parameters": {
                    "QueryString": aws_athena_named_query.notify_enriched.query,
                    "QueryExecutionContext": {
                      "Database": aws_athena_named_query.notify_enriched.database
                    },
                    "WorkGroup": aws_athena_named_query.notify_enriched.workgroup
                  },
                  "End": true,
                  "Catch": [
                    {
                      "ErrorEquals": ["States.ALL"],
                      "Next": "NotifyEnrichedAthenaFailed"
                    }
                  ]
                },
                "NotifyEnrichedAthenaFailed": {
                  "Type": "Pass",
                  "Result": "Notify Enriched Athena query failed",
                  "End": true
                },
                "GCNotifyJobFailed" : {
                  "Type" : "Pass",
                  "Result" : "GC Notify Glue job failed",
                  "End" : true
                }
              }
            },
            {
              "StartAt" : "StartFreshdeskJob",
              "States" : {
                "StartFreshdeskJob" : {
                  "Type" : "Task",
                  "Resource" : "arn:aws:states:::glue:startJobRun.sync",
                  "Parameters" : {
                    "JobName" : var.platform_support_freshdesk_name
                  },
                  "End" : true,
                  "Catch" : [
                    {
                      "ErrorEquals" : ["States.ALL"],
                      "Next" : "FreshdeskJobFailed"
                    }
                  ]
                },
                "FreshdeskJobFailed" : {
                  "Type" : "Pass",
                  "Result" : "Freshdesk Glue job failed",
                  "End" : true
                }
              }
            },
            {
              "StartAt" : "StartSalesforceJob",
              "States" : {
                "StartSalesforceJob" : {
                  "Type" : "Task",
                  "Resource" : "arn:aws:states:::glue:startJobRun.sync",
                  "Parameters" : {
                    "JobName" : var.bes_crm_salesforce_name
                  },
                  "End" : true,
                  "Catch" : [
                    {
                      "ErrorEquals" : ["States.ALL"],
                      "Next" : "SalesforceJobFailed"
                    }
                  ]
                },
                "SalesforceJobFailed" : {
                  "Type" : "Pass",
                  "Result" : "Salesforce Glue job failed",
                  "End" : true
                }
              }
            }
          ]
        },
        "AllJobsComplete" : {
          "Type" : "Succeed"
        }
      }
    }
  )
}