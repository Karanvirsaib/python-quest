CREATE TABLE `profiles` (
	`user_id` text PRIMARY KEY NOT NULL,
	`name` text NOT NULL,
	`goal` integer DEFAULT 1 NOT NULL
);
--> statement-breakpoint
CREATE TABLE `progress` (
	`user_id` text NOT NULL,
	`lesson_id` text NOT NULL,
	`code` text DEFAULT '' NOT NULL,
	`notes` text DEFAULT '' NOT NULL,
	`completed` integer DEFAULT false NOT NULL,
	`completed_at` text,
	`updated_at` text NOT NULL,
	PRIMARY KEY(`user_id`, `lesson_id`)
);
