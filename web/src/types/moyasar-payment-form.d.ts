// moyasar-payment-form ships moyasar.d.ts, but its package.json "exports" hides it from
// TypeScript. The part we use: Moyasar.init(config) (docs.moyasar.com, form configuration).
declare module "moyasar-payment-form" {
  const Moyasar: { init(config: Record<string, unknown>): void };
  export default Moyasar;
}
