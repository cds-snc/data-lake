# Changelog

## [1.2.4](https://github.com/cds-snc/data-lake/compare/v1.2.3...v1.2.4) (2025-05-21)


### Bug Fixes

* rollback notificationinterval one-time fix ([#265](https://github.com/cds-snc/data-lake/issues/265)) ([2a22b0c](https://github.com/cds-snc/data-lake/commit/2a22b0c12d53723c17c5d700f903364ea32b4b58))


### Miscellaneous Chores

* remove anomaly detection alarms ([#267](https://github.com/cds-snc/data-lake/issues/267)) ([d6b33e3](https://github.com/cds-snc/data-lake/commit/d6b33e3193238b166c0461380adde5d22e9cae00))

## [1.2.3](https://github.com/cds-snc/data-lake/compare/v1.2.2...v1.2.3) (2025-05-21)


### Bug Fixes

* added notificationinterval field ([#263](https://github.com/cds-snc/data-lake/issues/263)) ([a6b6378](https://github.com/cds-snc/data-lake/commit/a6b6378a23316ecf91fb4f0c3e0ce06a4277bccf))

## [1.2.2](https://github.com/cds-snc/data-lake/compare/v1.2.1...v1.2.2) (2025-05-16)


### Bug Fixes

* delay Notify ETL by 3 hours after RDS export ([#259](https://github.com/cds-snc/data-lake/issues/259)) ([a4fddd1](https://github.com/cds-snc/data-lake/commit/a4fddd1951797715d0c6ef35c2eb8898adb19109))
* increase the look back days for the `notification_history` load ([#261](https://github.com/cds-snc/data-lake/issues/261)) ([54dcc57](https://github.com/cds-snc/data-lake/commit/54dcc5793b58df2be1d7aaf41f30fc07a240b2be))

## [1.2.1](https://github.com/cds-snc/data-lake/compare/v1.2.0...v1.2.1) (2025-05-15)


### Documentation

* update Forms `deliveryemaildestination` description ([#256](https://github.com/cds-snc/data-lake/issues/256)) ([4efda9c](https://github.com/cds-snc/data-lake/commit/4efda9c978a7b6f512e04ccb14823e0771fbf6d0))


### Miscellaneous Chores

* enable anomaly detection alarm actions ([#258](https://github.com/cds-snc/data-lake/issues/258)) ([094890e](https://github.com/cds-snc/data-lake/commit/094890e549e5b407c15000e2885a22aa5cf49b79))

## [1.2.0](https://github.com/cds-snc/data-lake/compare/v1.1.0...v1.2.0) (2025-05-14)


### Features

* publish Freshdesk ETL CloudWatch metrics ([#252](https://github.com/cds-snc/data-lake/issues/252)) ([2b82a2e](https://github.com/cds-snc/data-lake/commit/2b82a2e8cb3e9b46c5ce3ec211943c9f01a61923))


### Bug Fixes

* add OIDC release role for production workflows ([#255](https://github.com/cds-snc/data-lake/issues/255)) ([4244ea5](https://github.com/cds-snc/data-lake/commit/4244ea5e87c879b42551fe0969d139c7a7958eee))

## [1.1.0](https://github.com/cds-snc/data-lake/compare/v1.0.0...v1.1.0) (2025-05-14)


### Features

* create anomaly detection alarms for GC Forms ([#251](https://github.com/cds-snc/data-lake/issues/251)) ([e3f2b59](https://github.com/cds-snc/data-lake/commit/e3f2b59193c1cbef14f470306aff8ae0a1f078b9))
* setup Release Please for prod deployments ([#250](https://github.com/cds-snc/data-lake/issues/250)) ([4566cf0](https://github.com/cds-snc/data-lake/commit/4566cf0b8c1a32b4e55dba79ae9fcb817b6e3b3b))
