SELECT id, file_ref
  FROM uploaded_file_content
  WHERE unprocessed = FALSE
    AND file_ref NOT IN (SELECT unnest($1::uuid[]));
