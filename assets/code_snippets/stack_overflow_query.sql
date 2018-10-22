SELECT TOP 20 p.score, p.favoritecount, p.viewcount, p.answercount, p.id AS [Post Link], p.title, p.body, p.tags
FROM posts p
WHERE PostTypeId = 1
GROUP BY p.score, p.favoritecount, p.viewcount, p.answercount, p.id, p.title, p.body, p.tags
ORDER BY p.score DESC