# Prime Backup Notify - Fork Information

## 关于本项目 / About This Project

**Prime Backup Notify** 是基于 [Prime Backup](https://github.com/TISUnion/PrimeBackup) (by Fallen_Breath) 的独立 fork 项目。

**Prime Backup Notify** is an independent fork of [Prime Backup](https://github.com/TISUnion/PrimeBackup) (by Fallen_Breath).

## 主要变更 / Major Changes

### 新增功能 / New Features

1. **任务通知推送 / Task Notifications**
   - 支持备份/回档任务的开始、成功、失败事件通知
   - Support for backup/restore task start, success, and failure notifications

2. **Webhook 支持 / Webhook Support**
   - 可配置多个 webhook 端点
   - 发送 JSON 格式的完整任务信息
   - Configure multiple webhook endpoints
   - Send complete task information in JSON format

3. **Bark 原生支持 / Native Bark Support**
   - 无需中转 webhook，直接推送到 Bark
   - 支持 URL 占位符、自定义等级与消息格式
   - 运维友好的默认消息格式
   - Direct push to Bark without relay webhook
   - Support URL placeholders, custom levels and message formatting
   - Ops-friendly default message format

4. **命令行测试 / Command-line Testing**
   - 新增 `!!pb test notify` 命令
   - 快速测试通知配置
   - New `!!pb test notify` command
   - Quick notification configuration testing

5. **完整文档 / Complete Documentation**
   - 中英文通知功能文档
   - 配置示例与最佳实践
   - Bilingual (EN/ZH) notification documentation
   - Configuration examples and best practices

### 技术变更 / Technical Changes

- 插件 ID: `prime_backup` → `prime_backup_notify`
- 包名保持不变以便于维护: `prime_backup` (unchanged for maintenance)
- 新增配置项: `notification` (root config)
- 新增权限项: `command.permission.test` (default: 4)

## 许可证 / License

本项目继承原项目的 **LGPL v3** 许可证。

This project inherits the **LGPL v3** license from the original project.

### 原作者 / Original Author

- **Fallen_Breath**
- GitHub: https://github.com/Fallen-Breath
- 原项目 / Original: https://github.com/TISUnion/PrimeBackup

### Fork 维护者 / Fork Maintainer

- **colorcard**
- GitHub: https://github.com/colorcard
- 本仓库 / This Fork: https://github.com/colorcard/PrimeBackupNotify

## 兼容性说明 / Compatibility

⚠️ **重要**: 由于插件 ID 已更改（`prime_backup_notify`），本 fork 版本与原版 Prime Backup **不兼容**，不能同时安装。

⚠️ **Important**: Due to the plugin ID change (`prime_backup_notify`), this fork is **incompatible** with the original Prime Backup and cannot be installed simultaneously.

### 从原版迁移 / Migration from Original

如果你想从原版 Prime Backup 迁移到本 fork：

If you want to migrate from the original Prime Backup to this fork:

1. 备份你的数据 / Backup your data
2. 卸载原版 Prime Backup / Uninstall original Prime Backup
3. 安装 Prime Backup Notify / Install Prime Backup Notify
4. 数据库和备份文件可以直接使用（配置文件路径会变化）/ Database and backup files can be used directly (config file path will change)
5. 配置文件路径变化：`config/prime_backup/` → `config/prime_backup_notify/`

## 致谢 / Acknowledgments

特别感谢 Fallen_Breath 创建并维护了优秀的 Prime Backup 项目。本 fork 的所有核心功能均来自原项目。

Special thanks to Fallen_Breath for creating and maintaining the excellent Prime Backup project. All core features of this fork come from the original project.

## 贡献 / Contributing

欢迎提交 Issue 和 Pull Request！

Issues and Pull Requests are welcome!

如果你的改进也适用于原版 Prime Backup，建议优先向原项目提交。

If your improvement is also applicable to the original Prime Backup, please consider contributing to the original project first.
