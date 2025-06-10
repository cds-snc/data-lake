# Changelog

## [1.6.0](https://github.com/cds-snc/data-lake/compare/v1.5.3...v1.6.0) (2025-06-10)


### Features

* add architecture diagrams for read/write operations ([#317](https://github.com/cds-snc/data-lake/issues/317)) ([0bd59d7](https://github.com/cds-snc/data-lake/commit/0bd59d7804eec97b57efcbd0c9b467f993ae6d1d))
* allow Superset prod IAM role access to Notify data ([#318](https://github.com/cds-snc/data-lake/issues/318)) ([fb3e00a](https://github.com/cds-snc/data-lake/commit/fb3e00ad05ba3f7fdcc240d6a74ab442ff395eac))


### Bug Fixes

* switch to logger.warn to support Glue Python version ([#312](https://github.com/cds-snc/data-lake/issues/312)) ([03c8bcc](https://github.com/cds-snc/data-lake/commit/03c8bcccf5d2638ce612f3cf45bede69e251d4c2))


### Miscellaneous Chores

* **deps:** update dependency requests to v2.32.4 [security] ([#316](https://github.com/cds-snc/data-lake/issues/316)) ([93e1b12](https://github.com/cds-snc/data-lake/commit/93e1b121cbdaa6397791694c47cca9fdbe9de0d5))

## [1.5.3](https://github.com/cds-snc/data-lake/compare/v1.5.2...v1.5.3) (2025-06-06)


### Bug Fixes

* CloudWatch anomaly metric pattern ([#307](https://github.com/cds-snc/data-lake/issues/307)) ([4fdb690](https://github.com/cds-snc/data-lake/commit/4fdb690bbec70b0c02b1b69c20483d9f9f98a546))

## [1.5.2](https://github.com/cds-snc/data-lake/compare/v1.5.1...v1.5.2) (2025-06-06)


### Bug Fixes

* create new alarm for data anomalies ([#304](https://github.com/cds-snc/data-lake/issues/304)) ([9b21b11](https://github.com/cds-snc/data-lake/commit/9b21b117f7891b233de2e95099d44b391ec77801))
* only display Spark ETL job errors ([#303](https://github.com/cds-snc/data-lake/issues/303)) ([c5643ea](https://github.com/cds-snc/data-lake/commit/c5643eaa6cb4a233041c2dc5234df746231d48d7))

## [1.5.1](https://github.com/cds-snc/data-lake/compare/v1.5.0...v1.5.1) (2025-06-05)


### Bug Fixes

* undo day partitioning ([#300](https://github.com/cds-snc/data-lake/issues/300)) ([1ca4452](https://github.com/cds-snc/data-lake/commit/1ca4452c69d0322e7cac62a133295fff719b0ad4))
* wrong gx path ([#302](https://github.com/cds-snc/data-lake/issues/302)) ([a67ff49](https://github.com/cds-snc/data-lake/commit/a67ff49c612de584573105e06659e01e88346a63))

## [1.5.0](https://github.com/cds-snc/data-lake/compare/v1.4.0...v1.5.0) (2025-06-04)


### Features

* Added Great Expectation for freshdesk ([#297](https://github.com/cds-snc/data-lake/issues/297)) ([5f1dfd4](https://github.com/cds-snc/data-lake/commit/5f1dfd4178febe493e12ad3b339de2ae35599464))
* Great Expectation Gc notify ([#296](https://github.com/cds-snc/data-lake/issues/296)) ([612484d](https://github.com/cds-snc/data-lake/commit/612484d7e9badb6498332f8141ec09285f307925))
* improved partitioning ([#290](https://github.com/cds-snc/data-lake/issues/290)) ([41dfd15](https://github.com/cds-snc/data-lake/commit/41dfd1567cbe42c52c8e4dbf812efc4987863335))


### Bug Fixes

* increased notify timeout ([#298](https://github.com/cds-snc/data-lake/issues/298)) ([adde205](https://github.com/cds-snc/data-lake/commit/adde205cf121dbe7ba8706a0481a8ba62d680b48))
* Notify ETL acceptable standard deviation ([#293](https://github.com/cds-snc/data-lake/issues/293)) ([716c53c](https://github.com/cds-snc/data-lake/commit/716c53cc7da04298d629d2776098a299cfc48a8a))


### Miscellaneous Chores

* **deps:** update all patch dependencies ([#295](https://github.com/cds-snc/data-lake/issues/295)) ([35c8612](https://github.com/cds-snc/data-lake/commit/35c8612d18e1843934006e527e8d26f220949842))
* **deps:** update mcr.microsoft.com/devcontainers/base:bullseye docker digest to c283798 ([#294](https://github.com/cds-snc/data-lake/issues/294)) ([25410a5](https://github.com/cds-snc/data-lake/commit/25410a56f5a0feedadb0d61a15833111c47146f0))
* suppress pip dependency resolver errors ([#291](https://github.com/cds-snc/data-lake/issues/291)) ([e6192b2](https://github.com/cds-snc/data-lake/commit/e6192b2b588043fedb48b52821d18e5bf6c10f2c))

## [1.4.0](https://github.com/cds-snc/data-lake/compare/v1.3.0...v1.4.0) (2025-05-28)


### Features

* add anomaly detection to Freshdesk dataset ([#288](https://github.com/cds-snc/data-lake/issues/288)) ([1e1ada9](https://github.com/cds-snc/data-lake/commit/1e1ada9f5c38d5a435e568d93c43c2ef6b498882))
* add anomaly detection to GC Forms dataset ([#285](https://github.com/cds-snc/data-lake/issues/285)) ([7e2662b](https://github.com/cds-snc/data-lake/commit/7e2662b10e5cb0671b71b0cfcc3f915051617847))
* Add new expectations ([#289](https://github.com/cds-snc/data-lake/issues/289)) ([bd94d11](https://github.com/cds-snc/data-lake/commit/bd94d119a45dd5b6c893420eaf6dae609f37969e))
* add Notify dataset anomaly detection ([#282](https://github.com/cds-snc/data-lake/issues/282)) ([48a3094](https://github.com/cds-snc/data-lake/commit/48a3094d2074d02f2c0aee20506cc8686bce4279))
* great expectations on Gc Forms ([#272](https://github.com/cds-snc/data-lake/issues/272)) ([ece4b47](https://github.com/cds-snc/data-lake/commit/ece4b4736bcb2e0c6fa6017f542ab48817a9626a))
* save raw GX results to raw data ([#286](https://github.com/cds-snc/data-lake/issues/286)) ([19ebd4b](https://github.com/cds-snc/data-lake/commit/19ebd4b36677dfe7c2c9fe357c7061160b0185e1))
* write site-docs to s3 bucket ([#283](https://github.com/cds-snc/data-lake/issues/283)) ([f84d9fb](https://github.com/cds-snc/data-lake/commit/f84d9fb67fdeddde7105501a55b0e5a9d3babb9d))


### Bug Fixes

* great expectation bugs ([#277](https://github.com/cds-snc/data-lake/issues/277)) ([0417d40](https://github.com/cds-snc/data-lake/commit/0417d405be088a3ff1c2d6f45cf69c3f0c316331))
* gx not saving output to s3 ([#287](https://github.com/cds-snc/data-lake/issues/287)) ([5174bf3](https://github.com/cds-snc/data-lake/commit/5174bf3155e16ec3754e16f55ba1893d03f3fe0d))
* Missing terraform output statement ([#275](https://github.com/cds-snc/data-lake/issues/275)) ([32fdae9](https://github.com/cds-snc/data-lake/commit/32fdae978202a6582a0d17d3fadc565c39f49a71))
* updated devcontainer tf version ([#284](https://github.com/cds-snc/data-lake/issues/284)) ([7175283](https://github.com/cds-snc/data-lake/commit/7175283413b51c32abe0a196cb7428282b54bcc9))


### Miscellaneous Chores

* **deps:** lock file maintenance ([#281](https://github.com/cds-snc/data-lake/issues/281)) ([fab7d07](https://github.com/cds-snc/data-lake/commit/fab7d071b19f29c1ddebd89a4d3cb24cf7e7df60))
* **deps:** update aws-actions/configure-aws-credentials action to v4.2.1 ([#278](https://github.com/cds-snc/data-lake/issues/278)) ([0fa19d2](https://github.com/cds-snc/data-lake/commit/0fa19d2d6b74a770145c0a27724860f0327bebbe))
* **deps:** update dependency boto3 to v1.38.18 ([#279](https://github.com/cds-snc/data-lake/issues/279)) ([322e672](https://github.com/cds-snc/data-lake/commit/322e672bb4eb03b5c67890abe4b0671ebdd1566f))
* **deps:** update terraform hashicorp/terraform to v1.12.0 ([#280](https://github.com/cds-snc/data-lake/issues/280)) ([8297c72](https://github.com/cds-snc/data-lake/commit/8297c72be47282a3330106d3ad4d61fb5fb98b2d))

## [1.3.0](https://github.com/cds-snc/data-lake/compare/v1.2.5...v1.3.0) (2025-05-22)


### Features

* add s3 bucket for great_expectations ([#270](https://github.com/cds-snc/data-lake/issues/270)) ([76ec6ae](https://github.com/cds-snc/data-lake/commit/76ec6ae2e7e47f0b78f2eed7cd1179d706d441c5))


### Bug Fixes

* skip missing Forms historical data error alarms ([#273](https://github.com/cds-snc/data-lake/issues/273)) ([219c57c](https://github.com/cds-snc/data-lake/commit/219c57c878f9e54970e57929f0f7b0c55140db18))

## [1.2.5](https://github.com/cds-snc/data-lake/compare/v1.2.4...v1.2.5) (2025-05-21)


### Bug Fixes

* CloudWatch metric filter alarms for ETL jobs ([#269](https://github.com/cds-snc/data-lake/issues/269)) ([dd0434d](https://github.com/cds-snc/data-lake/commit/dd0434d5ae5e47e430c3bef99c71c3e3fba7e1bc))


### Miscellaneous Chores

* **deps:** update all non-major github action dependencies ([#244](https://github.com/cds-snc/data-lake/issues/244)) ([b58f2bc](https://github.com/cds-snc/data-lake/commit/b58f2bc446071eb0487f0daefb3818ce0179c1d7))
* **deps:** update all patch dependencies ([#262](https://github.com/cds-snc/data-lake/issues/262)) ([4286396](https://github.com/cds-snc/data-lake/commit/4286396321a457b62237d3b136be92a69a769e80))
* **deps:** update mcr.microsoft.com/devcontainers/base:bullseye docker digest to 76a2d99 ([#243](https://github.com/cds-snc/data-lake/issues/243)) ([344a2ff](https://github.com/cds-snc/data-lake/commit/344a2fff6f914072f96333e6b37f517dee40b5e6))

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
