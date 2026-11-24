package tn.esprit.backend.dto;

import java.time.LocalDate;
import tn.esprit.backend.entity.ProjetDetaille;

/** What a client may write for a ProjetDetaille. The project link has its own route, so an edit keeps it. */
public record ProjetDetailleRequest(Long id, String description, String technologie,
                                    Double coutProvisoire, LocalDate dateDebut) {

    public ProjetDetaille toNewEntity() {
        ProjetDetaille d = new ProjetDetaille();
        applyTo(d);
        return d;
    }

    public void applyTo(ProjetDetaille d) {
        d.setDescription(description);
        d.setTechnologie(technologie);
        d.setCoutProvisoire(coutProvisoire);
        d.setDateDebut(dateDebut);
    }
}
