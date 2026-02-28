# Skill: coding-reference-hub

## Purpose
Coding reference skill untuk implementasi from-scratch. Ketika agent perlu contoh implementasi nyata (bukan teori), gunakan skill ini untuk routing cepat ke tutorial yang tepat.

**Primary resource**: https://github.com/codecrafters-io/build-your-own-x  
~300+ tutorial, 30 kategori, 25+ bahasa. Semua external links (blog, buku gratis, YouTube, GitHub repo).

---

## When to Load This Skill

Load skill ini ketika:
- User atau agent perlu implementasi sesuatu **dari scratch**
- Butuh contoh nyata / referensi kode untuk konsep low-level
- Menulis skill/tool baru dan butuh referensi implementasi
- Debugging sistem fundamental (DB, network, parser, dll)
- "Bagaimana X actually works?" → rebuildlah

---

## Quick Routing Table

### Database / Storage
| Want to build | Language | Link |
|---|---|---|
| SQLite clone | C | https://cstack.github.io/db_tutorial/ |
| Redis clone | C++ | https://build-your-own.org/redis/ |
| Redis clone | Python | https://www.reddit.com/r/redis/... (search BYO Redis Python) |
| Redis clone | Go | Multiple blog posts, search "build redis golang" |
| B+Tree | Go | https://build-your-own.org/database/ |

### Git
| Want to build | Language | Link |
|---|---|---|
| ugit | Python | https://www.leshenko.net/p/ugit/ |
| wyag | Python | https://wyag.thb.lt/ |
| gitlet | JavaScript | https://gitlet.maryrosecook.com/ |

### Web Server / HTTP
| Want to build | Language | Link |
|---|---|---|
| HTTP server | Python | https://ruslanspivak.com/lsbaws-part1/ |
| HTTP server | Go | https://cs.opensource.google/go/go |
| Express clone | Node.js | Multiple tutorials |
| HTTP from scratch | C | Various (search "build web server C from scratch") |

### Docker / Containers
| Want to build | Language | Link |
|---|---|---|
| Container runtime | C | https://blog.lizzie.io/linux-containers-in-500-loc.html |
| Container runtime | Go | https://www.infoq.com/articles/build-a-container-golang |
| Docker in Bash | Bash | https://github.com/p8952/bocker |

### Programming Language / Interpreter
| Want to build | Language | Link |
|---|---|---|
| Tree-walk interpreter | Java | https://craftinginterpreters.com/ (full book, free) |
| Bytecode VM | Java | https://craftinginterpreters.com/ (Part III) |
| Lisp interpreter | Any | https://github.com/kanaka/mal (50+ language impls) |
| Pratt parser | Tutorial | https://journal.stuffwithstuff.com/2011/03/19/pratt-parsers-expression-parsing-made-easy/ |
| LLVM tutorial | C++ | https://llvm.org/docs/tutorial/ |

### Shell
| Want to build | Language | Link |
|---|---|---|
| Shell | C | https://brennan.io/2015/01/16/write-a-shell-in-c/ |
| Shell | C | https://tutorial.ponylang.io/ (CS education) |
| Shell | Go | Multiple tutorials |
| Shell | Rust | https://www.joshmcguigan.com/blog/build-your-own-shell-rust/ |

### Neural Network / AI
| Want to build | Language | Link |
|---|---|---|
| NN from scratch | Python | https://victorzhou.com/blog/intro-to-neural-networks/ |
| GPT/LLM from scratch | Python | https://github.com/rasbt/LLMs-from-scratch |
| Neural Networks: Zero to Hero | Python | https://www.youtube.com/playlist?list=PLAqhIrjkxbuWI23v9cThsA9GvCAUhRvKZ (Karpathy) |
| Diffusion model | Python | https://huggingface.co/blog/annotated-diffusion |
| RAG from scratch | Python | Various (LangChain blog, LlamaIndex docs) |

### Front-end Framework
| Want to build | Language | Link |
|---|---|---|
| React clone (Didact) | JavaScript | https://pomb.us/build-your-own-react/ |
| React hooks | JavaScript | https://github.com/pomber/didact |
| Redux | JavaScript | Multiple tutorials |
| Virtual DOM | JavaScript | https://github.com/Matt-Esch/virtual-dom |

### Operating System
| Want to build | Language | Link |
|---|---|---|
| OS | Rust | https://os.phil-opp.com/ (Writing an OS in Rust, excellent) |
| OS | C/ASM | http://www.linuxfromscratch.org/ |
| OS (Raspberry Pi) | C | https://github.com/s-matyukevich/raspberry-pi-os |
| Kernel modules | C | https://sysprog21.github.io/lkmpg/ |

### Regex Engine
| Want to build | Language | Link |
|---|---|---|
| Regex (NFA-based) | Python | https://swtch.com/~rsc/regexp/regexp1.html |
| Regex | Go | Multiple tutorials |
| Regex | JavaScript | https://nickdrane.com/build-your-own-regex/ |
| Regex | C | https://www.cs.princeton.edu/courses/archive/spr09/cos333/beautiful.html |

### Search Engine
| Want to build | Language | Link |
|---|---|---|
| TF-IDF search | Python | Multiple tutorials |
| Vector search | Python | Various (usually paired with embeddings) |
| Full-text search | Go | Multiple tutorials |

### Web Browser
| Want to build | Language | Link |
|---|---|---|
| Browser (layout engine) | Python | https://browser.engineering/ (full book) |
| Layout engine (Robinson) | Rust | https://github.com/mbrubeck/robinson |

### BitTorrent Client
| Want to build | Language | Link |
|---|---|---|
| BitTorrent | Go | https://blog.jse.li/posts/torrent/ |
| BitTorrent | Python | https://markuseliasson.se/article/bittorrent-in-python/ |
| BitTorrent | Node.js | Multiple tutorials |

### Emulator / VM
| Want to build | Language | Link |
|---|---|---|
| CHIP-8 | C++ | https://austinmorlan.com/posts/chip8_emulator/ |
| CHIP-8 | Rust | https://github.com/ColinEberhardt/wasm-rust-chip8 |
| GameBoy | Rust | https://github.com/mvdnes/rboy |
| LC-3 VM | C | https://justinmeiners.github.io/lc3-vm/ |

### Text Editor
| Want to build | Language | Link |
|---|---|---|
| Kilo editor | C | https://viewsourcecode.org/snaptoken/kilo/ |
| Hecto | Rust | https://www.flenker.blog/hecto/ |

### Networking
| Want to build | Language | Link |
|---|---|---|
| TCP/IP stack | C | https://github.com/saminiir/level-ip |
| VPN | Various | https://github.com/nicowillis/go-simple-vpn |
| Network guide | C | https://beej.us/guide/bgnet/ (Beej's Guide, classic) |

---

## How to Use as Reference

### Pattern 1: Direct reference
```
"Need to implement X from scratch?"
→ Check routing table above
→ Point user/agent to specific tutorial link
→ Use as implementation reference, not copy-paste
```

### Pattern 2: Skill seed for new skills
```
"Building a new skill that needs low-level implementation knowledge?"
→ Read the relevant tutorial first
→ Extract key patterns, data structures, algorithms
→ Encode into new SKILL.md as domain knowledge
Example: Building a "custom-parser-skill" → Read Crafting Interpreters Part I first
```

### Pattern 3: Bookmark / quick lookup
```
"Forgot how X works internally?"
→ Load this skill
→ Find category → follow link
→ Skim for mental model, not full tutorial
```

---

## Full Category List (for quick reference)
3D Renderer | AI Model | Augmented Reality | BitTorrent Client | Blockchain | Bot | Command-Line Tool | Database | Docker | Emulator/VM | Front-end Framework | Game | Git | Memory Allocator | Network Stack | Neural Network | Operating System | Physics Engine | Processor | Programming Language | Regex Engine | Search Engine | Shell | Template Engine | Text Editor | Visual Recognition | Voxel Engine | Web Browser | Web Server | Uncategorized

**Full list**: https://github.com/codecrafters-io/build-your-own-x

---

## Quality Notes
- **Quality varies** — some are book-length polished resources (Crafting Interpreters, browser.engineering), others are short blog posts
- **Language preference**: Python/Go/Rust tutorials tend to be highest quality
- **Link freshness**: Some older links may be dead — check if 404, search for updated version
- **Best entries**: Crafting Interpreters, Writing an OS in Rust (phil-opp), Karpathy Zero to Hero, browser.engineering, Beej's Network Guide


---

## UI Templates & Web App References

Untuk membangun web dashboard/app production-ready (bukan from scratch), gunakan referensi berikut:

### Square UI — Next.js + shadcn/ui Layouts
**Source:** https://github.com/ln-dev7/square-ui  
**Live gallery:** https://square.lndev.me  
**Stack:** Next.js + TypeScript + shadcn/ui + Tailwind CSS | MIT | 4.9k⭐

Koleksi 20 template open-source dengan live demo + source code:

| Template | Demo | Gunakan untuk |
|----------|------|---------------|
| Dashboard 1-5 | [Gallery](https://square.lndev.me) | Stats, charts, tables, CRM, HR |
| Leads / Employees / Payrolls | [Gallery](https://square.lndev.me) | Data management + charts |
| Tasks / Calendar | [Gallery](https://square.lndev.me) | Task & scheduling UI |
| Chat | [Demo](https://square-ui-chat.vercel.app) | AI chat interface |
| Files / Bookmarks | [Gallery](https://square.lndev.me) | File/content manager |
| Maps / Rentals | [Gallery](https://square.lndev.me) | Map-based UI |

**Clone template:**
```bash
# Clone specific template
git clone https://github.com/ln-dev7/square-ui
cd square-ui/templates/dashboard-2
npm install && npm run dev
```

**Kapan pakai:** Codex nanobot butuh starter untuk web dashboard → pilih template yang paling mirip dengan target, adapt dari sana. Lebih cepat dari scratch.
