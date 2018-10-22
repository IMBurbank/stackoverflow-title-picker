#standardSQL
SELECT
  p.score,
  p.favorite_count,
  p.view_count,
  p.answer_count,
  CONCAT(
    "https://stackoverflow.com/questions/",
    CAST(p.id AS STRING),
    "/",
    REGEXP_REPLACE(
      REGEXP_REPLACE(LOWER(p.title), r"([^a-z\s]+)", ""),
      r"([\s]+)",
      "-"
    )
  ) as link,
  p.title,
  p.body,
  p.tags
FROM
  `bigquery-public-data.stackoverflow.posts_questions` p
GROUP BY
  p.score,
  p.favorite_count,
  p.view_count,
  p.answer_count,
  link,
  p.title,
  p.body,
  p.tags
HAVING
  p.score >= 5