SELECT c.id, c.file_ref
  FROM uploaded_file_content c
    LEFT JOIN uploaded_file f
    ON c.id = f.content_id
  WHERE f.content_id IS NULL
    AND c.file_ref NOT IN (SELECT unnest($1::uuid[]));
