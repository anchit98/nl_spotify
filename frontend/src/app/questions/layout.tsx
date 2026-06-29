import { QuestionsBundleProvider } from "@/components/QuestionsBundleProvider";

export default function QuestionsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <QuestionsBundleProvider>{children}</QuestionsBundleProvider>;
}
