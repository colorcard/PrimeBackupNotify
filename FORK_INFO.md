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

- 插件 ID: `prime_backup` (保持不变以兼容 MCDR 包名规范 / kept same for MCDR package naming compatibility)
- 插件名称: `Prime Backup Notify`
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

⚠️ **重要**: 本 fork 版本的插件名称为 **Prime Backup Notify**，但为了兼容 MCDR 的包名规范，插件 ID 保持为 `prime_backup`。

⚠️ **Important**: This fork is named **Prime Backup Notify**, but to comply with MCDR package naming conventions, the plugin ID remains `prime_backup`.

### 与原版的关系 / Relationship with Original

- **不能同时安装**：本 fork 与原版 Prime Backup 使用相同的插件 ID (`prime_backup`)，因此不能同时安装。
- **配置兼容**：配置文件路径相同 (`config/prime_backup/`)，数据库和备份文件可以直接使用。
- **功能增强**：在原版基础上新增了通知功能，保持所有原有功能不变。

- **Cannot coexist**: This fork and the original Prime Backup share the same plugin ID (`prime_backup`), so they cannot be installed simultaneously.
- **Config compatible**: Config file path remains `config/prime_backup/`, database and backup files can be used directly.
- **Feature enhancement**: Adds notification features on top of the original, keeping all existing features intact.

### 从原版迁移 / Migration from Original

如果你想从原版 Prime Backup 迁移到本 fork：

If you want to migrate from the original Prime Backup to this fork:

1. 停止服务器 / Stop the server
2. 备份你的数据（可选但推荐）/ Backup your data (optional but recommended)
3. 卸载原版 Prime Backup / Uninstall original Prime Backup
4. 安装 Prime Backup Notify / Install Prime Backup Notify
5. 配置文件路径相同，无需迁移 / Config path is the same, no migration needed
6. 如需使用通知功能，在配置中添加 `notification` 部分 / To use notifications, add `notification` section to config

## 致谢 / Acknowledgments

特别感谢 Fallen_Breath 创建并维护了优秀的 Prime Backup 项目。本 fork 的所有核心功能均来自原项目。

Special thanks to Fallen_Breath for creating and maintaining the excellent Prime Backup project. All core features of this fork come from the original project.

## 贡献 / Contributing

欢迎提交 Issue 和 Pull Request！

Issues and Pull Requests are welcome!

如果你的改进也适用于原版 Prime Backup，建议优先向原项目提交。

If your improvement is also applicable to the original Prime Backup, please consider contributing to the original project first.
