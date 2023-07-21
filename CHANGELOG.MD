## v2.0.2 - 2023-07-13

### Fixed

- #130 - Fix IP Fabric client snapshot reloading.
- #136 - Correct documentation on `nautobot-ssot` framework requirement.

## v2.0.1 - 2023-05-26

### Fixed

- #128 - Refresh client to ensure latest snapshots are loaded.
- #129 - Use new IP Fabric logo on the SSoT dashboard.
- #133 - Fix device interface import for interfaces with no description.

## v2.0.0 - 2023-01-27

### Added

- #117 - Add support for IP Fabric v6.

## Changed

- Version 2.0.0 of `nautobot-plugin-ssot-ipfabric` only supports IP Fabric version v6.0 and above.

## v1.0.0 - 2022-10-28

### Added

- #113 - Add support for IP Fabric v5.
- #111 - Remove site diagram feature. Not supported on IP Fabric v5.
- #108 - Extend Job form to get and initialize variables. 

## Changed

- Version 1.0.0 of `nautobot-plugin-ssot-ipfabric` only supports IP Fabric version v5.0 and above.

## v0.10.0 - 2022-06-08

### Added

- #100 - Add a Job option to select the reference snapshot to sync from.

## v0.9.6 - 2022-05-31

### Fixed

- #94 - Fix `primary_ip` usage in `interface` model, `delete` operations and `device_content` embedded `iframe`.

### Changed

- #94 - Make `ssot-safe-delete` log messages less noisy, using `debug` log level.

## v0.9.5 - 2022-05-11

### Added

- #89 - Add necessary assigned_object_type when assigned_object_id is defined.
- #85 - Migrate to ipfabric client library.

## v0.9.4 - 2022-01-26

### Added

- #76 - Refactor safe mode.
- #71 - Job name change.
