CREATE DATABASE olap_etl;

CREATE TABLE IF NOT EXISTS usuarios(
  id_usuario SERIAL PRIMARY KEY,
  nome VARCHAR(110) NOT NULL,
  idade INT NOT NULL,
  data_nascimento DATE
);

INSERT INTO usuarios(nome, idade, data_nascimento) 
VALUES 
('Ruan Silva', 20, '2006-04-16'),
('Kayo Silva', 20, '2006-04-16'),
('Matheus Diirr', 24, '2002-03-03');

SELECT u.nome, u.idade FROM usuarios u WHERE u.idade > 21;