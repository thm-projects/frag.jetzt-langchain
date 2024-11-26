INSERT INTO uploaded_file(content_id, account_id, name)
    VALUES ($1, $2, $3)
    ON CONFLICT (content_id, account_id, name) DO UPDATE
      SET name = $3
    RETURNING *;