resource "aws_sfn_state_machine" "etl_state_machine" {
  name     = "GlueOrchestrator"
  role_arn = aws_iam_role.sfn_role.arn
  definition = jsonencode(
    {
      "Comment" : "Orchestrates Glue jobs in parallel",
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
                  "Catch" : [
                    {
                      "ErrorEquals" : ["States.ALL"],
                      "Next" : "GCFormsJobFailed"
                    }
                  ],
                  "End" : true
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
                  "Catch" : [
                    {
                      "ErrorEquals" : ["States.ALL"],
                      "Next" : "GCNotifyJobFailed"
                    }
                  ],
                  "End" : true
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
                  "Catch" : [
                    {
                      "ErrorEquals" : ["States.ALL"],
                      "Next" : "FreshdeskJobFailed"
                    }
                  ],
                  "End" : true
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
                  "Catch" : [
                    {
                      "ErrorEquals" : ["States.ALL"],
                      "Next" : "SalesforceJobFailed"
                    }
                  ],
                  "End" : true
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