$pdf_mode = 1;

# Springer Nature keeps its BibTeX styles in bst/. Make them visible to
# BibTeX while preserving any search path already configured by the user.
$ENV{'BSTINPUTS'} = './bst//:' . ($ENV{'BSTINPUTS'} || '');

