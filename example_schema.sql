CREATE TABLE IF NOT EXISTS public.users(
  user_id INTEGER PRIMARY KEY NOT NULL,
  user_name VARCHAR(120) NOT NULL,
  user_email VARCHAR(150) NOT NULL
);

INSERT INTO public.users(user_id, user_name, user_email)
VALUES
(1, "test1", "test1@gmail.com")
(2, "carlos", "carlos@gmail.com")
(3, "jozias", "jozias@gmail.com");

SELECT
  u.user_name
  u.user_email
FROM
  public.users u
WHERE
  u.user_name
LIKE = "%test%";