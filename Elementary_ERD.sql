CREATE TABLE IF NOT EXISTS `CATEGORY` (
 `cat2_id` SMALLINT primary key,
 `cat1_name` VARCHAR(16) NOT NULL,
 `cat2_name` VARCHAR(16) NOT NULL,
 `platform_name` VARCHAR(8) NOT NULL
);

CREATE TABLE IF NOT EXISTS `NEWS` (
 `id` MEDIUMINT AUTO_INCREMENT primary key,
 `cat2_id` SMALLINT NOT NULL,
 `title` VARCHAR(256) NOT NULL,
 `press` VARCHAR(16),
 `writer` VARCHAR(32),
 `date_upload` DATETIME NOT NULL,
 `date_fix` DATETIME,
 `content` TEXT,
 `sticker` JSON NOT NULL,
 `url` VARCHAR(256) UNIQUE NOT NULL,
 FOREIGN KEY (cat2_id) references CATEGORY(cat2_id)
);

CREATE TABLE IF NOT EXISTS `USER` (
 `id` MEDIUMINT AUTO_INCREMENT primary key,
 `user_id` VARCHAR(8) UNIQUE NOT NULL,
 `user_name` VARCHAR(16)
);

ALTER TABLE USER MODIFY user_id VARCHAR(8) CHARACTER SET utf8 COLLATE utf8_bin NOT NULL;

CREATE TABLE IF NOT EXISTS `COMMENT` (
 `id` INT AUTO_INCREMENT primary key,
 `news_id` MEDIUMINT NOT NULL,
 `user_id` MEDIUMINT NOT NULL,
 `comment` TEXT NOT NULL,
 `date_upload` DATETIME NOT NULL,
 `date_fix` DATETIME,
 `good_cnt` SMALLINT,
 `bad_cnt` SMALLINT,
 FOREIGN KEY (news_id) references NEWS(id),
 FOREIGN KEY (user_id) references USER(id)
);