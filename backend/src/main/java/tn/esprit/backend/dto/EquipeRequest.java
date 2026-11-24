package tn.esprit.backend.dto;

import tn.esprit.backend.entity.Entreprise;
import tn.esprit.backend.entity.Equipe;

/**
 * What a client may write for an Equipe. The company is referenced by id; project
 * assignments are not part of the body (PUT /equipe/assign-projet), so an edit keeps them.
 */
public record EquipeRequest(Long id, String nom, String specialite, IdRef entreprise) {

    public Equipe toNewEntity() {
        Equipe e = new Equipe();
        applyTo(e);
        return e;
    }

    public void applyTo(Equipe e) {
        e.setNom(nom);
        e.setSpecialite(specialite);
        e.setEntreprise(entreprise == null || entreprise.id() == null
                ? null : Entreprise.builder().id(entreprise.id()).build());
    }
}
