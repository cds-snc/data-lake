# Operations / AWS / Cost and Usage Report

Dataset describing how much was spent on Amazon Web Services (AWS) by CDS.

Each row describes the cost of using a particular AWS service (i.e., a line item) within a billing period.

This dataset is represented in [Superset](https://superset.cds-snc.ca/) as the Physical dataset [`cost_usage_report_by_account`](https://superset.cds-snc.ca/explore/?datasource_type=table&datasource_id=68). All of the Virtual datasets in the "Operations / AWS / Cost and Usage" group are derived from it.

**Keywords:** AWS, Amazon, cost, usage, fees

---

[:information_source:  View the data pipeline](../../../pipelines/operations/aws/cost-and-usage-report.md)

## Provenance

This dataset is extracted daily from the [Cost and Usage Report 2.0 (CUR 2.0)](https://docs.aws.amazon.com/cur/latest/userguide/table-dictionary-cur2.html) table in [AWS Data Exports](https://docs.aws.amazon.com/cur/latest/userguide/what-is-data-exports.html). Additional information about business units are joined in the pipeline using the `tag_env` field.

More documentation on the pipeline can be found [here](../../../pipelines/operations/aws/cost-and-usage-report.md).

* **Updated:** Daily
* **Steward:** Platform Core Services
* **Contact:** [Pat Heard](mailto:patrick.heard@cds-snc.ca)
* **Location:** s3://cds-data-lake-transformed-production/operations/aws/cost-usage-report/data/billing_period=YYYY-MM/*.parquet

## Fields

Most field definitions are sourced directly from AWS's [Cost and Usage Report data dictionary](https://docs.aws.amazon.com/cur/latest/userguide/table-dictionary-cur2-reservation.html).

Many columns are grouped together with a common prefix. For example, the `product_comment`, `product_fee_code` and `product_fee_description` fields can all be grouped together as `product` columns.

A query to return example data can be found [here](examples/cost-and-usage-report.sql).

* **id** (integer) - AWS account ID for the line item.
* **arn** (string) - Amazon Resource Name of the AWS account for the resource being billed.
* **email** (string) - email associated with the AWS account for the line item.
* **name** (string) - name of the AWS account for the line item.
* **status** (string) - status of the line item's AWS account, one of "ACTIVE" or "INACTIVE".
* **joinedmethod** (string) - how the AWS account was was added to the AWS organization, one of "CREATED" or "INVITED".
* **joinedtimestamp** (string) - timestamp of AWS account's creation in UTC. Formatted as `YYYY-MM-DD HH:MM:SSz.`.

* `tag` columns, containing information about the member account business unit tags
    * **tag_env** (string) - tag assigned to the environment.
    * **tag_business_unit** (string) - business unit responsible for the service.
    * **tag_product** (string) - product that uses this service.
* `bill` columns, containing data about the bill for the billing period.
    * **bill_bill_type** (string) - type of bill that this report covers. One of:
        * "Anniversary" - line items for the services used during the month.
        * "Purchase" - line items for upfront service fees.
        * "Refund" - line items for refunds.
    * **bill_billing_entity** (string) - helps identify whether invoices are for AWS Marketplace or for purchases of other AWS services.
    * **bill_billing_period_end_date** (datetime) - end date of the billing period that is covered by this report, in UTC. The format is `YYYY-MM-DDTHH:mm:ssZ`.
    * **bill_billing_period_start_date** (datetime) - start date of the billing period that is covered by this report, in UTC. The format is `YYYY-MM-DDTHH:mm:ssZ`.
    * **bill_invoice_id** (string) - ID associated with a specific line item. Until the report is final, `bill_invoice_id` is blank.
    * **bill_invoicing_entity** (string) - AWS entity that issues the invoice.
    * **bill_payer_account_id** - account ID of the paying account. For an organization in AWS Organizations, this is the account ID of the management account.
    * **bill_payer_account_name** (string) - account name of the paying account. For an organization in AWS Organizations, this is the name of the management account.
* `discount` columns, containing information about any discounts being received
    * **discount_bundled_discount** (float) - bundled discount applied to the line item.
    * **discount_total_discount** (float) - sum of all the discount columns for the corresponding line item.
* `identity` columns, containing information that help identify a line item.
    * **identity_line_item_id** (string) - generated for each line item and is unique in a given partition.
    * **identity_time_interval** (string) - time interval that this line item applies to, in the format `YYYY-MM-DDTHH:mm:ssZ/YYYY-MM-DDTHH:mm:ssZ`
* `line_item` columns, contain data about cost, usage, type of usage, pricing rates, product name, and more.
    * **line_item_availability_zone** (string) - Availability Zone that hosts this line item. For example, us-east-1a or us-east-1b.
    * **line_item_blended_cost** (float) - `time_item_blended_rate` * `line_item_usage_amount`
    * **line_item_blended_rate** (float) - average cost incurred for each SKU across an organization.
    * **line_item_currency_code** (string) - currency that this line item is shown in. All AWS customers are billed in US dollars (`USD`) by default.
    * **line_item_legal_entity** (string) - Seller of Record of a specific product or service. In most cases, the invoicing entity and legal entity are the same.
    * **line_item_line_item_description** (string) - description of the line item type. For example, the description of a usage line item summarizes the type of usage incurred during a specific time period.
    * **line_item_line_item_type** (string) - type of charge covered by this line item. Common values are:
        * "Tax" - any taxes that AWS applied to bills. For example, VAT or US sales tax.
        * "Usage" - any usage that is charged at On-Demand Instance rates.
        * "Fee" - any upfront annual fee that are paid for subscriptions.
        * "Credit" - any credits that AWS applied to a bill. 
        * Nine other options not listed here. Refer to the [AWS Data Exports Dictionary](https://docs.aws.amazon.com/cur/latest/userguide/table-dictionary-cur2-line-item.html).
    * **line_item_net_unblended_cost** (float) - actual after-discount cost that you're paying for the line item. 
    * **line_item_net_unblended_rate** (string) - actual after-discount rate that you're paying for the line item. 
    * **line_item_normalization_factor** (float) - as long as the instance has shared tenancy, AWS can apply all Regional Linux or Unix Amazon EC2 and Amazon RDS RI discounts to all instance sizes in an instance family and AWS Region. This also applies to RI discounts for member accounts in an organization. All new and existing Amazon EC2 and Amazon RDS size-flexible RIs are sized according to a normalization factor, based on the instance size.
    * **line_item_normalized_usage_amount** (float) - amount of usage that you incurred, in normalized units, for size-flexible RIs. Calcuated as `line_item_usage_amount` * `line_item_normalization_factor`.
    * **line_item_operation** (string) - specific AWS operation covered by this line item. This describes the specific usage of the line item.
    * **line_item_product_code** (string) - code of the product measured.
    * **line_item_resource_id** (string) - the ID of the resource that has been provisioned.
    * **line_item_tax_type** (string) -  type of tax that AWS applied to this line item.
    * **line_item_unblended_cost** (float) - `line_item_unblended_rate` * `line_item_usage_amount`.
    * **line_item_unblended_rate** (string) - unblended rate is the rate associated with an individual account's service usage.
    * **line_item_usage_account_id** (string) - account ID of the account that used this line item.
    * **line_item_usage_account_name** (string) - account name that used this line item.
    * **line_item_usage_amount** (float) - amount of usage that incurred during the specified time period.
    * **line_item_usage_end_date** (datetime) - end date and time for the corresponding line item in UTC, exclusive. The format is `YYYY-MM-DDTHH:mm:ssZ`.
    * **line_item_usage_start_date** (datetime) - start date and time for the corresponding line item in UTC, exclusive. The format is `YYYY-MM-DDTHH:mm:ssZ`.
    * **line_item_usage_type** (string) - usage details of the line item.
* `pricing` columns, contain data about the pricing for a line item.
    * **pricing_currency** (string) - currency that the pricing data is shown in.
    * **pricing_lease_contract_length** (string) - length of time that your RI is reserved for.
    * **pricing_offering_class** (string) - offering class of the Reserved Instance.
    * **pricing_public_on_demand_cost** (float) -  total cost for the line item based on public On-Demand Instance rates. 
    * **pricing_public_on_demand_rate** (string) - public On-Demand Instance rate in this billing period for the specific line item of usage.
    * **pricing_purchase_option** (string) - how this line item is paid for, one of "All Upfront", "Partial Upfront", and "No Upfront".
    * **pricing_rate_code** (string) - unique code for a product/offer/pricing-tier combination. 
    * **pricing_rate_id** (string) - ID of the rate for a line item.
    * **pricing_term** - (string) whether the AWS usage is "Reserved" or "On-Demand".
    * **pricing_unit** (string) - pricing unit AWS used to calculate your usage cost.
* `product` columns contain data about the product that is being charged in the line item.
    * **product_from_location_type** (string) - describes the location type where the usage originated from.
    * **product_from_region_code** (string) - describes the source Region code for the AWS service.
    * **product_instance_family** (string) - describes the Amazon EC2 instance family.
    * **product_instance_type** (string) - describes the instance type, size, and family, which define the CPU, networking, and storage capacity of the instance.
    * **product_instancesku** (string) - SKU (stock keeping unit) of the product instance
    * **product_location** (string) - describes the Region that the Amazon S3 bucket resides in.
    * **product_location_type** (string) - describes the endpoint of your task.
    * **product_operation** (string) - describes the specific AWS operation that this line item covers.
    * **product_pricing_unit** (string) - smallest billing unit for an AWS service. For example, 0.01c per API call.
    * **product_product_family** (string) - category for the type of product.
    * **product_region_code** (string) - a Region is a physical location around the world where data centers are clustered. AWS calls each group of logical data centers an Availability Zone (AZ). 
    * **product_servicecode** (string) - identifies the specific AWS service to the customer as a unique short abbreviation.
    * **product_sku** (string) - unique code for a product. The SKU is created by combining `line_item_product_code`, `line_item_usage_type`, and `product_operation`.
    * **product_to_location** (string) - describes the location usage destination.
    * **product_to_location_type** (string) - describes the destination location of the service usage.
    * **product_to_region_code** (string) - describes the source Region code for the AWS service.
    * **product_usagetype** (string) - describes the usage details of the line item.
* `reservation` columns contain data about a reservation that applies to the line item. **As of December 2024, the way CDS uses AWS means that most of these fields are blank.**
    * **reservation_amortized_upfront_cost_for_usage** (float) - initial upfront payment for all upfront RIs and partial upfront RIs (Reserved Instance) amortized for usage time.
    * **reservation_amortized_upfront_fee_for_billing_period** (float) - escribes how much of the upfront fee for this reservation is costing you for the billing period.
    * **reservation_availability_zone** (string) - Availability Zone of the resource that is associated with this line item.
    * **reservation_effective_cost** (float) - sum of both the upfront and hourly rate of an RI, averaged into an effective hourly rate.
    * **reservation_end_time** (string) - end date of the associated RI lease term.
    * **reservation_modification_status** (string) - describes whether the RI lease was modified or if it is unaltered. One of "Original", "System", "Manual", or "ManualWithData".
    * **reservation_net_amortized_upfront_cost_for_usage** (float) - initial upfront payment for All Upfront RIs and Partial Upfront RIs amortized for usage time, if applicable
    * **reservation_net_amortized_upfront_fee_for_billing_period** (float) -  cost of the reservation's upfront fee for the billing period.
    * **reservation_net_effective_cost** (float) - sum of both the upfront fee and the hourly rate of the RI, averaged into an effective hourly rate. 
    * **reservation_net_recurring_fee_for_usage** (float) - after-discount cost of the recurring usage fee.
    * **reservation_net_unused_amortized_upfront_fee_for_billing_period** (float) - net unused amortized upfront fee for the billing period.
    * **reservation_net_unused_recurring_fee** (float) - recurring fees associated with unused reservation hours for Partial Upfront and No Upfront RIs after discounts.
    * **reservation_net_upfront_value** (float) - upfront value of the RI with discounts applied.
    * **reservation_normalized_units_per_reservation** (string) - number of normalized units for each instance of a reservation subscription.
    * **reservation_number_of_reservations** (string) - number of reservations that are covered by this subscription.
    * **reservation_recurring_fee_for_usage** (float) - recurring fee amortized for usage time, for partial upfront RIs and no upfront RIs. 
    * **reservation_reservation_a_r_n** (string) - Amazon Resource Name (ARN) of the RI that this line item benefited from. This is also called the "RI Lease ID".
    * **reservation_start_time** (string) - start date of the term of the associated Reserved Instance.
    * **reservation_subscription_id** (string) - unique identifier that maps a line item with the associated offer
    * **reservation_total_reserved_normalized_units** (string) - total number of reserved normalized units for all instances for a reservation subscription.
    * **reservation_total_reserved_units** (string) - total number of reserved units for all instances for a reservation subscription.
    * **reservation_units_per_reservation** (string) - total number of units per reservation
    * **reservation_unused_amortized_upfront_fee_for_billing_period** (float) - amortized-upfront-fee-for-billing-period-column amortized portion of the initial upfront fee for all upfront RIs and partial upfront RIs.
    * **reservation_unused_normalized_unit_quantity** (float) - number of unused normalized units for a size-flexible Regional RI that you didn't use during this billing period.
    * **reservation_unused_quantity** (float) - number of RI hours that you didn't use during this billing period.
    * **reservation_unused_recurring_fee** (float) - recurring fees associated with your unused reservation hours for partial upfront and no upfront RIs. 
    * **reservation_upfront_value** (float) - upfront price paid for an AWS Reserved Instance.
* `savings_plan` columns contain data about savings plans that apply to the line item. **As of December 2024, the way CDS uses AWS means that most of these fields are blank.**
    * **savings_plan_end_time** (string) - expiration date for the Savings Plan agreement.
    * **savings_plan_instance_type_family** (string) - instance family that is associated with the specified usage.
    * **savings_plan_net_amortized_upfront_commitment_for_billing_period** (float) - cost of a Savings Plan subscription upfront fee for the billing period. 
    * **savings_plan_net_recurring_commitment_for_billing_period** (float) - net unblended cost of the Savings Plan fee. 
    * **savings_plan_net_savings_plan_effective_cost** (float) - effective cost for Savings Plans, which is the usage divided by the fees.
    * **savings_plan_offering_type** (string) - describes the type of Savings Plan purchased.
    * **savings_plan_payment_option** (string) - payment options available for your Savings Plan.
    * **savings_plan_purchase_term** (string) - describes the duration, or term, of the Savings Plan.
    * **savings_plan_recurring_commitment_for_billing_period** (float) - monthly recurring fee for your Savings Plan subscriptions. 
    * **savings_plan_region** (string) - AWS Region (geographic area) that hosts your AWS services.
    * **savings_plan_savings_plan_a_r_n** (string) - unique Savings Plan identifier.
    * **savings_plan_savings_plan_effective_cost** (float) -  proportion of the Savings Plan monthly commitment amount (upfront and recurring) that is allocated to each usage line.
    * **savings_plan_savings_plan_rate** (float) - Savings Plan rate for the usage.
    * **savings_plan_start_time** (string) - start date of the Savings Plan agreement.
    * **savings_plan_total_commitment_to_date** (float) - total amortized upfront commitment and recurring commitment to date, for that hour.
* `split_line_item` columns
    * **split_line_item_actual_usage** (float) - usage for vCPU or memory (based on lineItem/UsageType) you incurred for the specified time period for the Amazon ECS task or Kubernetes pod.
    * **split_line_item_net_split_cost** (float) - effective cost for Amazon ECS tasks or Kubernetes pods after all discounts have been applied. 
    * **split_line_item_net_unused_cost** (float) - effective unused cost for Amazon ECS tasks or Kubernetes pods after all discounts have been applied. 
    * **split_line_item_parent_resource_id** (float) - resource ID of the parent EC2 instance associated with the Amazon ECS task or Amazon EKS pod.
    * **split_line_item_public_on_demand_split_cost** (float) - cost for vCPU or memory (based on lineItem/UsageType) allocated for the time period to the Amazon ECS task or Kubernetes pod based on public On-Demand Instance rates.
    * **split_line_item_public_on_demand_unused_cost** (float) - unused cost for vCPU or memory (based on lineItem/UsageType) allocated for the time period to the Amazon ECS task or Kubernetes pod based on public On-Demand Instance rates. 
    * **split_line_item_reserved_usage** (float) - usage for vCPU or memory (based on lineItem/UsageType) that have been configured for the specified time period for the Amazon ECS task or Kubernetes pod.
    * **split_line_item_split_cost** (float) - cost for vCPU or memory (based on lineItem/UsageType) allocated for the time period to the Amazon ECS task or Kubernetes pod
    * **split_line_item_split_usage** (float) - usage for vCPU or memory (based on lineItem/UsageType) allocated for the specified time period to the Amazon ECS task or Kubernetes pod. 
    * **split_line_item_split_usage_ratio** (float) - ratio of vCPU or memory (based on lineItem/UsageType) allocated to the Amazon ECS task or Kubernetes pod compared to the overall CPU or memory available on the EC2 instance 
    * **split_line_item_unused_cost** (float) - unused cost for vCPU or memory (based on lineItem/UsageType) allocated for the time period to the Amazon ECS task or Kubernetes pod.
* **billing_period** (string) - billing period for the line item, in the format `mmm-YYYY`

## Notes

Many of the columns, especially in the `savings_plan`, `reservation` and `split_line_item` groups of columns, are rarely populated due to the way that CDS uses AWS.
