# =============================================================================
# OsdagBridge — Report Theme
# LaTeX preamble: document class, packages, colors, table spacing, margins,
# custom commands. Single source of truth for report styling.
# =============================================================================

from osdagbridge.core.reports.report_utils import _tex

# ── Brand color ─────────────────────────────────────────────────────────────
OSDAG_GREEN_HEX = "91B014"

# ── Page margins ─────────────────────────────────────────────────────────────
PAGE_MARGIN = "1in"

# ── Table spacing (default, used across most chapters) ──────────────────────
TABCOLSEP = "6pt"
ARRAYSTRETCH = "1.12"
ARRAYRULEWIDTH = "0.5pt"
EXTRAROWHEIGHT = "0.6pt"
LTPRE = "0pt"
LTPOST = "6pt"

# ── Table spacing (dense variants, reused by several chapters' wide tables) ──
TABCOLSEP_DENSE = "3.5pt"   # chap7, chap8
TABCOLSEP_COMPACT = "4pt"   # chap2, chap5

# ── Header / footer ──────────────────────────────────────────────────────────
# The footnote line ("* Software default value") is reserved on every page,
# whether shown or blanked out with \hphantom, so the footer occupies the
# same height on every page instead of toggling between two vspace amounts
# depending on page content. FOOTSKIP must be wide enough to hold that
# reserved line plus the rule and page-number line below it.
HEADRULE_HEIGHT = "1pt"
FOOTER_ORG_LINE = r"Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay"
FOOTRULE_GAP = "6pt"
SD_FOOTNOTE_GAP = "4pt"
FOOTSKIP = "40pt"
NO_FOOTNOTE_VSPACE = "-8pt"

# Minimum vertical space required before starting a table, so a table never
# begins with only a few lines left at the bottom of a page.
LONGTABLE_NEEDSPACE = "8\\baselineskip"


# ═══════════════════════════════════════════════════════════════════════════════
# PREAMBLE
# ═══════════════════════════════════════════════════════════════════════════════

def preamble(project_name, job_number, report_date, report_version='Rev 0'):
    pn = _tex(project_name)
    jn = _tex(job_number)
    rd = _tex(report_date)
    rv = _tex(report_version)
    return r"""
\documentclass[12pt,a4paper]{report}

% Packages
\usepackage[a4paper, margin=""" + PAGE_MARGIN + r""", footskip=""" + FOOTSKIP + r"""]{geometry}
\usepackage{graphicx}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{booktabs}
\usepackage{array}
\usepackage{tabularx}
\usepackage{float}
\usepackage{fancyhdr}
\usepackage[hidelinks]{hyperref}
\usepackage{xcolor}
\usepackage{setspace}
\usepackage{enumitem}
\usepackage{caption}

\captionsetup{
    labelfont=bf,
    justification=raggedright,
    singlelinecheck=false,
    format=plain
}
\usepackage{subcaption}
\usepackage{multirow}
\usepackage{colortbl}
\usepackage{longtable}
\setlength{\LTleft}{\fill}
\setlength{\LTright}{\fill}
\usepackage{titlesec}
\usepackage{titletoc}
\usepackage{lastpage}
\usepackage{makecell}
\usepackage{etoolbox}
\usepackage{needspace}

\numberwithin{table}{chapter}
\numberwithin{figure}{chapter}
% Table layout and spacing: consistent padding, row height, and longtable pre/post skips
\setlength{\tabcolsep}{""" + TABCOLSEP + r"""}
\renewcommand{\arraystretch}{""" + ARRAYSTRETCH + r"""}
\setlength{\LTpre}{""" + LTPRE + r"""}
\setlength{\LTpost}{""" + LTPOST + r"""}
% Table rules (outline thickness) and small extra row height for clarity
\setlength{\arrayrulewidth}{""" + ARRAYRULEWIDTH + r"""}
\setlength{\extrarowheight}{""" + EXTRAROWHEIGHT + r"""}

% Prevent tables from starting with only a few lines left at the bottom of
% a page: if less than LONGTABLE_NEEDSPACE remains, break to the next page first.
\BeforeBeginEnvironment{table}{\needspace{""" + LONGTABLE_NEEDSPACE + r"""}}
\BeforeBeginEnvironment{longtable}{\needspace{""" + LONGTABLE_NEEDSPACE + r"""}}

\definecolor{osdagGreen}{HTML}{""" + OSDAG_GREEN_HEX + r"""}

\fancypagestyle{main}{
  \fancyhf{}
  \fancyhead[L]{""" + pn + r""" $|$ """ + jn + r"""}
  \fancyhead[R]{""" + rd + r""" $|$ """ + rv + r"""}
  \fancyfoot[L]{""" + FOOTER_ORG_LINE + r"""}
  \fancyfoot[R]{Page \thepage\ of \pageref{LastPage}}
  \renewcommand{\headrule}{\color{osdagGreen}\hrule width\headwidth height """ + HEADRULE_HEIGHT + r""" \vspace{2pt}}
  \renewcommand{\footrule}{%
    \hbox to \headwidth{\textcolor{black}{\footnotesize\textit{%
      \ifbool{hasSDonPage}{* Software default value}{\hphantom{* Software default value}}%
    }}\hfil}%
    \vspace{""" + SD_FOOTNOTE_GAP + r"""}%
    \color{osdagGreen}\hrule width\headwidth height """ + HEADRULE_HEIGHT + r""" \vspace{""" + FOOTRULE_GAP + r"""}%
  }
}
\fancypagestyle{plain}{
  \fancyhf{}
  \fancyhead[L]{""" + pn + r""" $|$ """ + jn + r"""}
  \fancyhead[R]{""" + rd + r""" $|$ """ + rv + r"""}
  \fancyfoot[L]{""" + FOOTER_ORG_LINE + r"""}
  \fancyfoot[R]{Page \thepage\ of \pageref{LastPage}}
  \renewcommand{\headrule}{\color{osdagGreen}\hrule width\headwidth height """ + HEADRULE_HEIGHT + r""" \vspace{2pt}}
  \renewcommand{\footrule}{%
    \hbox to \headwidth{\textcolor{black}{\footnotesize\textit{%
      \ifbool{hasSDonPage}{* Software default value}{\hphantom{* Software default value}}%
    }}\hfil}%
    \vspace{""" + SD_FOOTNOTE_GAP + r"""}%
    \color{osdagGreen}\hrule width\headwidth height """ + HEADRULE_HEIGHT + r""" \vspace{""" + FOOTRULE_GAP + r"""}%
  }
}
\fancypagestyle{firstpage}{
  \fancyhf{}
  \renewcommand{\headrulewidth}{0pt}
  \fancyfoot[L]{""" + FOOTER_ORG_LINE + r"""}
  \fancyfoot[R]{Page \thepage\ of \pageref{LastPage}}
  \renewcommand{\footrule}{\vspace{""" + NO_FOOTNOTE_VSPACE + r"""}\color{osdagGreen}\hrule width\headwidth height """ + HEADRULE_HEIGHT + r""" \vspace{""" + FOOTRULE_GAP + r"""}}
}
\pagestyle{main}
\setstretch{1.15}

% Custom Commands
\newcommand{\placeholder}[1]{\textit{\textless #1\textgreater}}
\newcommand{\todo}[1]{\colorbox{yellow}{TODO: #1}}
\newcolumntype{L}[1]{>{\raggedright\arraybackslash}p{#1}}
\newcolumntype{C}[1]{>{\centering\arraybackslash}p{#1}}
\newcolumntype{R}[1]{>{\raggedleft\arraybackslash}p{#1}}

% Software-default asterisk
\newcommand{\sdstar}{\textsuperscript{*}}
\newbool{hasSDonPage}
\boolfalse{hasSDonPage}
\newcommand{\markSD}{\global\booltrue{hasSDonPage}}
\renewcommand{\sdstar}{\textsuperscript{*}\markSD{}}
\AddToHook{shipout/before}{\global\boolfalse{hasSDonPage}}

\title{\Large\textbf{OsdagBridge} \\ \normalsize Open Source Software for Steel Girder Bridge Design \\ \vspace{2cm} \large Design Report}
\author{}
\date{}

\begin{document}
"""
