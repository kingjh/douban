CREATE TABLE `pz_douban_movie` (
  `film_id` int(11) NOT NULL DEFAULT '0' COMMENT '豆瓣影片id',
  `title` varchar(255) NOT NULL COMMENT '电影名',
  `score` decimal(9,2) NOT NULL DEFAULT '0.00' COMMENT '评分',
  `num` int(11) NOT NULL DEFAULT '0' COMMENT '评价人数',
  `link` varchar(255) NOT NULL DEFAULT '' COMMENT '详情链接',
  `type` tinyint(1) NOT NULL DEFAULT '0' COMMENT '类型(0=不明|1=电影|2=电视剧)',
  `directors` varchar(255) NOT NULL DEFAULT '' COMMENT '导演',
  `screenwriters` varchar(255) NOT NULL DEFAULT '' COMMENT '编剧',
  `actors` text NOT NULL COMMENT '主演',
  `tags` varchar(255) NOT NULL COMMENT '类型(0=不明|1=电影|2=电视剧)',
  `time` varchar(255) NOT NULL DEFAULT '' COMMENT '上映时间',
  `length` varchar(255) NOT NULL DEFAULT '' COMMENT '片长',
  `updated_at` int(11) NOT NULL DEFAULT '0' COMMENT '抓取时间',
  `created_at` int(11) NOT NULL DEFAULT '0' COMMENT '创建时间',
  PRIMARY KEY (`film_id`),
  KEY `idx_film_id` (`film_id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='影片表';
