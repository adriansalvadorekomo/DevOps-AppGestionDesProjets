package tn.esprit.backend.controller;

import lombok.AllArgsConstructor;
import org.springframework.web.bind.annotation.*;
import tn.esprit.backend.dto.EquipeRequest;
import tn.esprit.backend.exception.ApiErrors;
import tn.esprit.backend.entity.Equipe;
import tn.esprit.backend.service.IEquipeService;

import java.util.List;

@RestController
@RequestMapping("/equipe")
@AllArgsConstructor
public class EquipeController {

    IEquipeService equipeService;

    @PostMapping("/add")
    public Equipe addEquipe(@RequestBody EquipeRequest request) {
        return equipeService.addEquipe(request.toNewEntity());
    }

    /** Loads the stored record and changes only the fields the client may write. */
    @PutMapping("/update")
    public Equipe updateEquipe(@RequestBody EquipeRequest request) {
        if (request.id() == null) {
            throw ApiErrors.idRequired();
        }
        Equipe existing = equipeService.getEquipeById(request.id());
        if (existing == null) {
            throw ApiErrors.notFound("Equipe", request.id());
        }
        request.applyTo(existing);
        return equipeService.updateEquipe(existing);
    }

    @DeleteMapping("/delete/{id}")
    public void deleteEquipe(@PathVariable Long id) {
        equipeService.deleteEquipe(id);
    }

    @GetMapping("/get/{id}")
    public Equipe getEquipeById(@PathVariable Long id) {
        return equipeService.getEquipeById(id);
    }

    @GetMapping("/all")
    public List<Equipe> getAllEquipes() {
        return equipeService.getAllEquipes();
    }

    @GetMapping("/by-entreprise/{entrepriseId}")
    public List<Equipe> getEquipesByEntreprise(@PathVariable Long entrepriseId) {
        return equipeService.getEquipesByEntreprise(entrepriseId);
    }

    @PutMapping("/assign-entreprise/{equipeId}/{entrepriseId}")
    public Equipe assignEquipeToEntreprise(@PathVariable Long equipeId, @PathVariable Long entrepriseId) {
        return equipeService.assignEquipeToEntreprise(equipeId, entrepriseId);
    }

    @PutMapping("/assign-projet/{equipeId}/{projetId}")
    public Equipe assignEquipeToProjet(@PathVariable Long equipeId, @PathVariable Long projetId) {
        return equipeService.assignEquipeToProjet(equipeId, projetId);
    }
}
