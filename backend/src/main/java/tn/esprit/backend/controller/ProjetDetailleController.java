package tn.esprit.backend.controller;

import lombok.AllArgsConstructor;
import org.springframework.web.bind.annotation.*;
import tn.esprit.backend.dto.ProjetDetailleRequest;
import tn.esprit.backend.exception.ApiErrors;
import tn.esprit.backend.entity.ProjetDetaille;
import tn.esprit.backend.service.IProjetDetailleService;

import java.util.List;

@RestController
@RequestMapping("/projet-detaille")
@AllArgsConstructor
public class ProjetDetailleController {

    IProjetDetailleService projetDetailleService;

    @PostMapping("/add")
    public ProjetDetaille addProjetDetaille(@RequestBody ProjetDetailleRequest request) {
        return projetDetailleService.addProjetDetaille(request.toNewEntity());
    }

    /** Loads the stored record and changes only the fields the client may write. */
    @PutMapping("/update")
    public ProjetDetaille updateProjetDetaille(@RequestBody ProjetDetailleRequest request) {
        if (request.id() == null) {
            throw ApiErrors.idRequired();
        }
        ProjetDetaille existing = projetDetailleService.getProjetDetailleById(request.id());
        if (existing == null) {
            throw ApiErrors.notFound("ProjetDetaille", request.id());
        }
        request.applyTo(existing);
        return projetDetailleService.updateProjetDetaille(existing);
    }

    @DeleteMapping("/delete/{id}")
    public void deleteProjetDetaille(@PathVariable Long id) {
        projetDetailleService.deleteProjetDetaille(id);
    }

    @GetMapping("/get/{id}")
    public ProjetDetaille getProjetDetailleById(@PathVariable Long id) {
        return projetDetailleService.getProjetDetailleById(id);
    }

    @GetMapping("/all")
    public List<ProjetDetaille> getAllProjetsDetailles() {
        return projetDetailleService.getAllProjetsDetailles();
    }

    @GetMapping("/by-projet/{projetId}")
    public List<ProjetDetaille> getProjetDetaillesByProjet(@PathVariable Long projetId) {
        return projetDetailleService.getProjetDetaillesByProjet(projetId);
    }

    @PutMapping("/assign-projet/{projetDetailleId}/{projetId}")
    public ProjetDetaille assignProjetDetailleToProjet(@PathVariable Long projetDetailleId, @PathVariable Long projetId) {
        return projetDetailleService.assignProjetDetailleToProjet(projetDetailleId, projetId);
    }
}
