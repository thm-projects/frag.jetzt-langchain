WITH inserted AS (
    INSERT INTO uploaded_file_content(hash, file_ref, unprocessed)
      VALUES ($1, $2, $3)
      ON CONFLICT DO NOTHING
      RETURNING *
) SELECT * FROM inserted
UNION 
(SELECT * FROM uploaded_file_content where hash = $1);
