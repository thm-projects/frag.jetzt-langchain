SELECT *
  FROM uploaded_file_content
  WHERE unprocessed = true
    AND file_ref NOT IN (SELECT unnest($1::uuid[]));
