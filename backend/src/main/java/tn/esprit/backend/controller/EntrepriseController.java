package tn.esprit.backend.controller;

import lombok.AllArgsConstructor;
import org.springframework.web.bind.annotation.*;
import tn.esprit.backend.dto.EntrepriseRequest;
import tn.esprit.backend.exception.ApiErrors;
import tn.esprit.backend.entity.Entreprise;
import tn.esprit.backend.service.IEntrepriseService;

import java.util.List;

@RestController
@RequestMapping("/entreprise")
@AllArgsConstructor
public class EntrepriseController {

    IEntrepriseService entrepriseService;

    @PostMapping("/add")
    public Entreprise addEntreprise(@RequestBody EntrepriseRequest request) {
        return entrepriseService.addEntreprise(request.toNewEntity());
    }

    /** Loads the stored record and changes only the fields the client may write. */
    @PutMapping("/update")
    public Entreprise updateEntreprise(@RequestBody EntrepriseRequest request) {
        if (request.id() == null) {
            throw ApiErrors.idRequired();
        }
        Entreprise existing = entrepriseService.getEntrepriseById(request.id());
        if (existing == null) {
            throw ApiErrors.notFound("Entreprise", request.id());
        }
        request.applyTo(existing);
        return entrepriseService.updateEntreprise(existing);
    }

    @DeleteMapping("/delete/{id}")
    public void deleteEntreprise(@PathVariable Long id) {
        entrepriseService.deleteEntreprise(id);
    }

    @GetMapping("/get/{id}")
    public Entreprise getEntrepriseById(@PathVariable Long id) {
        return entrepriseService.getEntrepriseById(id);
    }

    @GetMapping("/all")
    public List<Entreprise> getAllEntreprises() {
        return entrepriseService.getAllEntreprises();
    }
}
