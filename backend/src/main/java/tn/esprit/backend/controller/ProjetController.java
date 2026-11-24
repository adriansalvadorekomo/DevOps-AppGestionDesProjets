package tn.esprit.backend.controller;

import lombok.AllArgsConstructor;
import org.springframework.web.bind.annotation.*;
import tn.esprit.backend.dto.ProjetRequest;
import tn.esprit.backend.exception.ApiErrors;
import tn.esprit.backend.entity.Projet;
import tn.esprit.backend.service.IProjetService;

import java.util.List;

@RestController
@RequestMapping("/projet")
@AllArgsConstructor
public class ProjetController {

    IProjetService projetService;

    @PostMapping("/add")
    public Projet addProjet(@RequestBody ProjetRequest request) {
        return projetService.addProjet(request.toNewEntity());
    }

    /** Loads the stored record and changes only the fields the client may write. */
    @PutMapping("/update")
    public Projet updateProjet(@RequestBody ProjetRequest request) {
        if (request.id() == null) {
            throw ApiErrors.idRequired();
        }
        Projet existing = projetService.getProjetById(request.id());
        if (existing == null) {
            throw ApiErrors.notFound("Projet", request.id());
        }
        request.applyTo(existing);
        return projetService.updateProjet(existing);
    }

    @DeleteMapping("/delete/{id}")
    public void deleteProjet(@PathVariable Long id) {
        projetService.deleteProjet(id);
    }

    @GetMapping("/get/{id}")
    public Projet getProjetById(@PathVariable Long id) {
        return projetService.getProjetById(id);
    }

    @GetMapping("/all")
    public List<Projet> getAllProjets() {
        return projetService.getAllProjets();
    }
}
