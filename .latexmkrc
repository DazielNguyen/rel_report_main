$pdf_mode = 1;

# Springer Nature keeps its BibTeX styles in bst/. Make them visible to
# BibTeX while preserving any search path already configured by the user.
if ($^O eq 'MSWin32') {
  # MiKTeX BibTeX on Windows may not inherit BSTINPUTS from the
  # latexmk process, so copy the .bst files to the working directory
  # where BibTeX always finds them.
  foreach my $f (glob('bst/*.bst')) {
    (my $base = $f) =~ s{.*[/\\]}{};
    system('copy', '/Y', $f, $base) == 0 or warn "Cannot copy $f: $!";
  }
} else {
  $ENV{'BSTINPUTS'} = './bst//:' . ($ENV{'BSTINPUTS'} || '');
}
