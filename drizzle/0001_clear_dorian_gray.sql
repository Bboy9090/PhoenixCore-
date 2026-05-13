CREATE TABLE `audit_logs` (
	`id` int AUTO_INCREMENT NOT NULL,
	`userId` int,
	`action` varchar(128) NOT NULL,
	`resourceType` varchar(128) NOT NULL,
	`resourceId` varchar(128) NOT NULL,
	`details` json,
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	CONSTRAINT `audit_logs_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `bootcamp_drivers` (
	`id` int AUTO_INCREMENT NOT NULL,
	`driverId` varchar(128) NOT NULL,
	`name` varchar(255) NOT NULL,
	`category` varchar(128) NOT NULL,
	`version` varchar(64) NOT NULL,
	`downloadUrl` text NOT NULL,
	`fileSize` decimal(10,2) NOT NULL,
	`compatibleModels` json NOT NULL,
	`releaseDate` timestamp,
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `bootcamp_drivers_id` PRIMARY KEY(`id`),
	CONSTRAINT `bootcamp_drivers_driverId_unique` UNIQUE(`driverId`)
);
--> statement-breakpoint
CREATE TABLE `deployment_logs` (
	`id` int AUTO_INCREMENT NOT NULL,
	`deploymentId` int NOT NULL,
	`timestamp` timestamp NOT NULL DEFAULT (now()),
	`level` enum('info','warning','error','debug') NOT NULL DEFAULT 'info',
	`message` longtext NOT NULL,
	CONSTRAINT `deployment_logs_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `deployment_policies` (
	`id` int AUTO_INCREMENT NOT NULL,
	`policyKey` varchar(128) NOT NULL,
	`value` json NOT NULL,
	`description` text,
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `deployment_policies_id` PRIMARY KEY(`id`),
	CONSTRAINT `deployment_policies_policyKey_unique` UNIQUE(`policyKey`)
);
--> statement-breakpoint
CREATE TABLE `deployments` (
	`id` int AUTO_INCREMENT NOT NULL,
	`deploymentId` varchar(128) NOT NULL,
	`recipeId` int NOT NULL,
	`deviceId` int,
	`userId` int NOT NULL,
	`status` enum('pending','building','deploying','completed','failed','cancelled') NOT NULL DEFAULT 'pending',
	`progressPercent` int NOT NULL DEFAULT 0,
	`startedAt` timestamp,
	`completedAt` timestamp,
	`errorMessage` text,
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `deployments_id` PRIMARY KEY(`id`),
	CONSTRAINT `deployments_deploymentId_unique` UNIQUE(`deploymentId`)
);
--> statement-breakpoint
CREATE TABLE `devices` (
	`id` int AUTO_INCREMENT NOT NULL,
	`deviceId` varchar(128) NOT NULL,
	`name` varchar(255) NOT NULL,
	`status` enum('online','offline','error','deploying') NOT NULL DEFAULT 'offline',
	`hardwareProfile` json NOT NULL,
	`osType` enum('windows','macos','linux') NOT NULL,
	`macAddress` varchar(17),
	`ipAddress` varchar(45),
	`lastHeartbeat` timestamp,
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `devices_id` PRIMARY KEY(`id`),
	CONSTRAINT `devices_deviceId_unique` UNIQUE(`deviceId`)
);
--> statement-breakpoint
CREATE TABLE `health_metrics` (
	`id` int AUTO_INCREMENT NOT NULL,
	`serviceName` varchar(128) NOT NULL,
	`status` enum('healthy','degraded','offline') NOT NULL DEFAULT 'offline',
	`latency` int,
	`uptime` decimal(5,2),
	`lastCheck` timestamp NOT NULL DEFAULT (now()),
	CONSTRAINT `health_metrics_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `notification_preferences` (
	`id` int AUTO_INCREMENT NOT NULL,
	`userId` int NOT NULL,
	`emailOnDeploymentComplete` boolean NOT NULL DEFAULT true,
	`emailOnDeploymentFailed` boolean NOT NULL DEFAULT true,
	`emailOnFleetAlert` boolean NOT NULL DEFAULT false,
	`inAppNotifications` boolean NOT NULL DEFAULT true,
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `notification_preferences_id` PRIMARY KEY(`id`),
	CONSTRAINT `notification_preferences_userId_unique` UNIQUE(`userId`)
);
--> statement-breakpoint
CREATE TABLE `notifications` (
	`id` int AUTO_INCREMENT NOT NULL,
	`notificationId` varchar(128) NOT NULL,
	`userId` int NOT NULL,
	`type` enum('deployment_complete','deployment_failed','fleet_alert','system_alert') NOT NULL,
	`title` varchar(255) NOT NULL,
	`content` text NOT NULL,
	`relatedResourceId` varchar(128),
	`read` boolean NOT NULL DEFAULT false,
	`readAt` timestamp,
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	CONSTRAINT `notifications_id` PRIMARY KEY(`id`),
	CONSTRAINT `notifications_notificationId_unique` UNIQUE(`notificationId`)
);
--> statement-breakpoint
CREATE TABLE `recipes` (
	`id` int AUTO_INCREMENT NOT NULL,
	`recipeId` varchar(128) NOT NULL,
	`userId` int NOT NULL,
	`name` varchar(255) NOT NULL,
	`description` text,
	`osImage` json NOT NULL,
	`drivers` json NOT NULL,
	`tools` json NOT NULL,
	`estimatedSize` decimal(10,2) NOT NULL,
	`compatibility` json,
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `recipes_id` PRIMARY KEY(`id`),
	CONSTRAINT `recipes_recipeId_unique` UNIQUE(`recipeId`)
);
--> statement-breakpoint
CREATE TABLE `relay_nodes` (
	`id` int AUTO_INCREMENT NOT NULL,
	`nodeId` varchar(128) NOT NULL,
	`name` varchar(255) NOT NULL,
	`location` varchar(255),
	`status` enum('healthy','degraded','offline') NOT NULL DEFAULT 'offline',
	`syncStatus` enum('synced','syncing','out_of_sync') NOT NULL DEFAULT 'out_of_sync',
	`cacheHealth` decimal(5,2) DEFAULT '0.00',
	`lastHeartbeat` timestamp,
	`configuredAt` timestamp,
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `relay_nodes_id` PRIMARY KEY(`id`),
	CONSTRAINT `relay_nodes_nodeId_unique` UNIQUE(`nodeId`)
);
--> statement-breakpoint
ALTER TABLE `users` MODIFY COLUMN `role` enum('user','admin','owner') NOT NULL DEFAULT 'user';--> statement-breakpoint
CREATE INDEX `audit_user_idx` ON `audit_logs` (`userId`);--> statement-breakpoint
CREATE INDEX `audit_action_idx` ON `audit_logs` (`action`);--> statement-breakpoint
CREATE INDEX `driver_category_idx` ON `bootcamp_drivers` (`category`);--> statement-breakpoint
CREATE INDEX `log_deployment_idx` ON `deployment_logs` (`deploymentId`);--> statement-breakpoint
CREATE INDEX `deployment_status_idx` ON `deployments` (`status`);--> statement-breakpoint
CREATE INDEX `deployment_device_idx` ON `deployments` (`deviceId`);--> statement-breakpoint
CREATE INDEX `deployment_user_idx` ON `deployments` (`userId`);--> statement-breakpoint
CREATE INDEX `device_status_idx` ON `devices` (`status`);--> statement-breakpoint
CREATE INDEX `device_id_idx` ON `devices` (`deviceId`);--> statement-breakpoint
CREATE INDEX `health_service_idx` ON `health_metrics` (`serviceName`);--> statement-breakpoint
CREATE INDEX `pref_user_idx` ON `notification_preferences` (`userId`);--> statement-breakpoint
CREATE INDEX `notification_user_idx` ON `notifications` (`userId`);--> statement-breakpoint
CREATE INDEX `notification_read_idx` ON `notifications` (`read`);--> statement-breakpoint
CREATE INDEX `recipe_user_idx` ON `recipes` (`userId`);--> statement-breakpoint
CREATE INDEX `relay_status_idx` ON `relay_nodes` (`status`);--> statement-breakpoint
CREATE INDEX `role_idx` ON `users` (`role`);