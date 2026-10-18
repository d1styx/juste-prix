-- Table des meilleurs scores : un joueur, son nombre d'essais, la date
CREATE TABLE IF NOT EXISTS scores (
  id      INT AUTO_INCREMENT PRIMARY KEY,
  pseudo  VARCHAR(30) NOT NULL,
  essais  INT NOT NULL,
  cree_le TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index pour trier rapidement le classement par nombre d'essais
CREATE INDEX idx_scores_essais ON scores (essais);
