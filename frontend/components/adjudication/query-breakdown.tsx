import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { type QuerySet } from '@/lib/types';

export function QueryBreakdown({ querySet }: { querySet?: QuerySet }) {
  if (!querySet) return null;

  return (
    <Accordion type="single" collapsible className="rounded-lg border border-slate-200 px-4">
      <AccordionItem value="queries" className="border-b-0">
        <AccordionTrigger>How the system searched</AccordionTrigger>
        <AccordionContent>
          <div className="space-y-3 text-sm text-slate-600">
            {querySet.supporting ? (
              <p>
                <span className="font-medium text-slate-800">Support query:</span> {querySet.supporting}
              </p>
            ) : null}
            {querySet.opposing ? (
              <p>
                <span className="font-medium text-slate-800">Oppose query:</span> {querySet.opposing}
              </p>
            ) : null}
            {querySet.alternative ? (
              <p>
                <span className="font-medium text-slate-800">Alternative query:</span> {querySet.alternative}
              </p>
            ) : null}
          </div>
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  );
}
