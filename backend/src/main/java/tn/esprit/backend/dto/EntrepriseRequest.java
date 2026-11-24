package tn.esprit.backend.dto;

import tn.esprit.backend.entity.Entreprise;

/** What a client may write for an Entreprise: no id on create, no relations. */
public record EntrepriseRequest(Long id, String nom, String adresse) {

    public Entreprise toNewEntity() {
        Entreprise e = new Entreprise();
        applyTo(e);
        return e;
    }

    public void applyTo(Entreprise e) {
        e.setNom(nom);
        e.setAdresse(adresse);
    }
}
