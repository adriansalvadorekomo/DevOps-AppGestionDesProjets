package tn.esprit.backend.dto;

import tn.esprit.backend.entity.Projet;

/** What a client may write for a Projet: the subject only; teams and details have their own routes. */
public record ProjetRequest(Long id, String sujet) {

    public Projet toNewEntity() {
        Projet p = new Projet();
        applyTo(p);
        return p;
    }

    public void applyTo(Projet p) {
        p.setSujet(sujet);
    }
}
